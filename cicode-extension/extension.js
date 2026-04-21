const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

const INTERPRETER = path.join(__dirname, 'interpreter', 'cicode.py');
const DEBUG_ADAPTER = path.join(__dirname, 'interpreter', 'debug_adapter.py');

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

/** Show a quick-pick of functions from the given file text, with the first one pre-selected. */
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
            terminal.sendText(`python3 "${INTERPRETER}" run ${fileArgs} -c ${funcName}; echo; read -p "Press Enter to close..." && exit`);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('cicode.runAllFiles', async () => {
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
            terminal.sendText(`python3 "${INTERPRETER}" run ${ciFiles} -c ${funcName}; echo; read -p "Press Enter to close..." && exit`);
        })
    );

    // Provide a default debug config automatically — no launch.json needed
    context.subscriptions.push(
        vscode.debug.registerDebugConfigurationProvider('cicode', {
            async resolveDebugConfiguration(folder, config) {
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
            return new vscode.DebugAdapterExecutable('python3', [DEBUG_ADAPTER]);
        }
    };
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('cicode', factory)
    );
}

function deactivate() {}

module.exports = { activate, deactivate };

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

/** Show a quick-pick of functions from the given file text, with the first one pre-selected. */
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
            terminal.sendText(`python3 "${INTERPRETER}" run ${fileArgs} -c ${funcName}; echo; read -p "Press Enter to close..." && exit`);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('cicode.runAllFiles', async () => {
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
            terminal.sendText(`python3 "${INTERPRETER}" run ${ciFiles} -c ${funcName}; echo; read -p "Press Enter to close..." && exit`);
        })
    );

    const factory = {
        createDebugAdapterDescriptor(session) {
            return new vscode.DebugAdapterExecutable('python3', [DEBUG_ADAPTER]);
        }
    };
    context.subscriptions.push(
        vscode.debug.registerDebugAdapterDescriptorFactory('cicode', factory)
    );
}

function deactivate() {}

module.exports = { activate, deactivate };
