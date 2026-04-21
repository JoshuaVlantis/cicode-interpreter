const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

const INTERPRETER = path.join(__dirname, 'interpreter', 'cicode.py');
const DEBUG_ADAPTER = path.join(__dirname, 'interpreter', 'debug_adapter.py');

const isWindows = process.platform === 'win32';
const python = isWindows ? 'python' : 'python3';

const { execSync } = require('child_process');

/**
 * Check that Python and required packages are available.
 * Shows an error notification with install instructions if anything is missing.
 * Returns false if checks fail, true if all good.
 */
async function checkPrerequisites() {
    // 1. Python itself
    try {
        execSync(`${python} --version`, { stdio: 'ignore' });
    } catch {
        const action = await vscode.window.showErrorMessage(
            `CiCode: Python not found. Please install Python 3 and ensure it is on your PATH.`,
            'Download Python'
        );
        if (action === 'Download Python') {
            vscode.env.openExternal(vscode.Uri.parse('https://www.python.org/downloads/'));
        }
        return false;
    }

    // 2. Required packages
    const missing = [];
    for (const pkg of ['pymssql', 'tkinter']) {
        try {
            execSync(`${python} -c "import ${pkg}"`, { stdio: 'ignore' });
        } catch {
            missing.push(pkg);
        }
    }

    if (missing.length > 0) {
        const installable = missing.filter(p => p !== 'tkinter');
        const tkMissing = missing.includes('tkinter');

        let msg = `CiCode: Missing package(s): ${missing.join(', ')}.`;
        const actions = [];

        if (installable.length > 0) {
            actions.push('Install via pip');
        }
        if (tkMissing) {
            actions.push('Show tkinter fix');
        }

        const action = await vscode.window.showErrorMessage(msg, ...actions);

        if (action === 'Install via pip') {
            const terminal = vscode.window.createTerminal('CiCode Setup');
            terminal.show();
            const flag = isWindows ? '' : '--break-system-packages';
            terminal.sendText(`${python} -m pip install ${installable.join(' ')} ${flag}`);
        }
        if (action === 'Show tkinter fix') {
            if (isWindows || process.platform === 'darwin') {
                vscode.window.showInformationMessage(
                    'tkinter is included with standard Python on Windows/macOS. Re-install Python from python.org if it is missing.'
                );
            } else {
                const terminal = vscode.window.createTerminal('CiCode Setup');
                terminal.show();
                terminal.sendText('sudo apt-get install -y python3-tk');
            }
        }
        return false;
    }

    return true;
}

/** Build a terminal run command with a cross-platform "press enter to close" */
function buildRunCmd(fileArgs, funcName) {
    const run = `${python} "${INTERPRETER}" run ${fileArgs} -c ${funcName}`;
    if (isWindows) {
        // PowerShell (VSCode default on Windows)
        return `${run}; Write-Host ""; Read-Host "Press Enter to close"`;
    } else {
        return `${run}; echo; read -p "Press Enter to close..." && exit`;
    }
}

/** Parse all FUNCTION names from a .ci file's text, in order. */
function parseFunctions(text) {
    const regex = /^\s*(?:INT|REAL|STRING|OBJECT|QUALITY|TIMESTAMP)?\s*FUNCTION\s+(\w+)\s*\(/gim;
    const names = [];
    let m;
    while ((m = regex.exec(text)) !== null) {
        names.push(m[1]);
    }
    return names;
}

/** Show a quick-pick of functions from the given file text. */
async function pickFunction(fileText) {
    const funcs = parseFunctions(fileText);
    if (funcs.length === 0) {
        return vscode.window.showInputBox({ prompt: 'CiCode function to run' });
    }
    return vscode.window.showQuickPick(funcs, {
        placeHolder: 'Select or type a CiCode function to run',
        title: 'CiCode: Run Function'
    });
}

function activate(context) {
    // On activation: quietly check prerequisites and warn if broken
    checkPrerequisites().catch(() => {});

    // Exposed as a command so launch.json inputs can call it via "type": "command"
    context.subscriptions.push(
        vscode.commands.registerCommand('cicode.pickFunction', async () => {
            const editor = vscode.window.activeTextEditor;
            const text = editor ? editor.document.getText() : '';
            return pickFunction(text);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('cicode.runFunction', async () => {
            if (!await checkPrerequisites()) return;
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            const activeFile = editor.document.fileName;
            const wsRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
                        || path.dirname(activeFile);
            const ciFiles = fs.readdirSync(wsRoot)
                .filter(f => f.endsWith('.ci'))
                .map(f => `"${path.join(wsRoot, f)}"`)
                .join(' ');
            const fileArgs = ciFiles || `"${activeFile}"`;
            const funcName = await pickFunction(editor.document.getText());
            if (!funcName) return;
            const terminal = vscode.window.createTerminal('CiCode');
            terminal.show();
            terminal.sendText(buildRunCmd(fileArgs, funcName));
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('cicode.runAllFiles', async () => {
            if (!await checkPrerequisites()) return;
            const folders = vscode.workspace.workspaceFolders;
            if (!folders) return;
            const wsRoot = folders[0].uri.fsPath;
            const ciFiles = fs.readdirSync(wsRoot)
                .filter(f => f.endsWith('.ci'))
                .map(f => `"${path.join(wsRoot, f)}"`)
                .join(' ');
            if (!ciFiles) {
                vscode.window.showWarningMessage('No .ci files found in workspace root.');
                return;
            }
            const editor = vscode.window.activeTextEditor;
            const text = editor ? editor.document.getText() : '';
            const funcName = await pickFunction(text);
            if (!funcName) return;
            const terminal = vscode.window.createTerminal('CiCode');
            terminal.show();
            terminal.sendText(buildRunCmd(ciFiles, funcName));
        })
    );

    // Provide a default debug config automatically — no launch.json needed
    context.subscriptions.push(
        vscode.debug.registerDebugConfigurationProvider('cicode', {
            async resolveDebugConfiguration(folder, config) {
                if (!await checkPrerequisites()) return undefined;
                if (!config.type && !config.request && !config.name) {
                    const editor = vscode.window.activeTextEditor;
                    if (!editor) return undefined;
                    const wsRoot = folder?.uri.fsPath || path.dirname(editor.document.fileName);
                    const ciFiles = fs.readdirSync(wsRoot).filter(f => f.endsWith('.ci'));
                    const funcName = await pickFunction(editor.document.getText());
                    if (!funcName) return undefined;
                    return {
                        type: 'cicode',
                        request: 'launch',
                        name: 'CiCode Debug',
                        program: editor.document.fileName,
                        function: funcName,
                        additionalFiles: ciFiles
                            .filter(f => f !== path.basename(editor.document.fileName))
                            .map(f => path.join(wsRoot, f))
                    };
                }
                if (!config.function) {
                    const editor = vscode.window.activeTextEditor;
                    const text = editor ? editor.document.getText() : '';
                    config.function = await pickFunction(text);
                }
                return config;
            }
        })
    );

    const factory = {
        createDebugAdapterDescriptor(session) {
            return new vscode.DebugAdapterExecutable(python, [DEBUG_ADAPTER]);
        }
    };
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('cicode', factory)
    );
}

function deactivate() {}

module.exports = { activate, deactivate };

