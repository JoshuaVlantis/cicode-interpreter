import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { execSync } from "child_process";

const isWindows = process.platform === "win32";
const python = isWindows ? "python" : "python3";

function getInterpreterPath(context: vscode.ExtensionContext): string {
  return context.asAbsolutePath(path.join("interpreter", "cicode.py"));
}

function getDebugAdapterPath(context: vscode.ExtensionContext): string {
  return context.asAbsolutePath(path.join("interpreter", "debug_adapter.py"));
}

async function checkPrerequisites(): Promise<boolean> {
  try {
    execSync(`${python} --version`, { stdio: "ignore" });
  } catch {
    const action = await vscode.window.showErrorMessage(
      `CiCode: Python not found. Please install Python 3 and ensure it is on your PATH.`,
      "Download Python",
    );
    if (action === "Download Python") {
      vscode.env.openExternal(
        vscode.Uri.parse("https://www.python.org/downloads/"),
      );
    }
    return false;
  }

  const missing: string[] = [];
  for (const pkg of ["pymssql", "tkinter"]) {
    try {
      execSync(`${python} -c "import ${pkg}"`, { stdio: "ignore" });
    } catch {
      missing.push(pkg);
    }
  }

  if (missing.length > 0) {
    const installable = missing.filter((p) => p !== "tkinter");
    const tkMissing = missing.includes("tkinter");
    const msg = `CiCode: Missing package(s): ${missing.join(", ")}.`;
    const actions: string[] = [];
    if (installable.length > 0) actions.push("Install via pip");
    if (tkMissing) actions.push("Show tkinter fix");

    const action = await vscode.window.showErrorMessage(msg, ...actions);
    if (action === "Install via pip") {
      const terminal = vscode.window.createTerminal("CiCode Setup");
      terminal.show();
      const flag = isWindows ? "" : "--break-system-packages";
      terminal.sendText(
        `${python} -m pip install ${installable.join(" ")} ${flag}`,
      );
    }
    if (action === "Show tkinter fix") {
      if (isWindows || process.platform === "darwin") {
        vscode.window.showInformationMessage(
          "tkinter is included with standard Python on Windows/macOS. Re-install Python from python.org if it is missing.",
        );
      } else {
        const terminal = vscode.window.createTerminal("CiCode Setup");
        terminal.show();
        terminal.sendText("sudo apt-get install -y python3-tk");
      }
    }
    return false;
  }
  return true;
}

function buildRunCmd(
  interpreterPath: string,
  fileArgs: string,
  funcName: string,
): string {
  const run = `${python} "${interpreterPath}" run ${fileArgs} -c ${funcName}`;
  if (isWindows) {
    return `${run}; Write-Host ""; Read-Host "Press Enter to close"`;
  } else {
    return `${run}; echo; read -p "Press Enter to close..." && exit`;
  }
}

function parseFunctions(text: string): string[] {
  const regex =
    /^\s*(?:INT|REAL|STRING|OBJECT|QUALITY|TIMESTAMP)?\s*FUNCTION\s+(\w+)\s*\(/gim;
  const names: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = regex.exec(text)) !== null) {
    names.push(m[1]);
  }
  return names;
}

async function pickFunction(fileText: string): Promise<string | undefined> {
  const funcs = parseFunctions(fileText);
  if (funcs.length === 0) {
    return vscode.window.showInputBox({ prompt: "CiCode function to run" });
  }
  return vscode.window.showQuickPick(funcs, {
    placeHolder: "Select or type a CiCode function to run",
    title: "CiCode: Run Function",
  });
}

export function registerRunCommands(
  context: vscode.ExtensionContext,
): vscode.Disposable[] {
  const cmds: vscode.Disposable[] = [];
  const INTERPRETER = getInterpreterPath(context);
  const DEBUG_ADAPTER = getDebugAdapterPath(context);

  // Exposed for launch.json inputs
  cmds.push(
    vscode.commands.registerCommand("cicode.pickFunction", async () => {
      const editor = vscode.window.activeTextEditor;
      const text = editor ? editor.document.getText() : "";
      return pickFunction(text);
    }),
  );

  // ▶ Run button: runs via terminal (no debug)
  cmds.push(
    vscode.commands.registerCommand("cicode.runFunction", async () => {
      if (!(await checkPrerequisites())) return;
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      await vscode.workspace.saveAll(false);
      const activeFile = editor.document.fileName;
      const wsRoot =
        vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ||
        path.dirname(activeFile);
      const ciFiles = fs
        .readdirSync(wsRoot)
        .filter((f) => f.endsWith(".ci"))
        .map((f) => `"${path.join(wsRoot, f)}"`)
        .join(" ");
      const fileArgs = ciFiles || `"${activeFile}"`;
      const funcName = await pickFunction(editor.document.getText());
      if (!funcName) return;
      const terminal = vscode.window.createTerminal("CiCode");
      terminal.show();
      terminal.sendText(buildRunCmd(INTERPRETER, fileArgs, funcName));
    }),
  );

  // Run across all .ci files in workspace
  cmds.push(
    vscode.commands.registerCommand("cicode.runAllFiles", async () => {
      if (!(await checkPrerequisites())) return;
      const folders = vscode.workspace.workspaceFolders;
      if (!folders) return;
      await vscode.workspace.saveAll(false);
      const wsRoot = folders[0].uri.fsPath;
      const ciFiles = fs
        .readdirSync(wsRoot)
        .filter((f) => f.endsWith(".ci"))
        .map((f) => `"${path.join(wsRoot, f)}"`)
        .join(" ");
      if (!ciFiles) {
        vscode.window.showWarningMessage("No .ci files found in workspace root.");
        return;
      }
      const editor = vscode.window.activeTextEditor;
      const text = editor ? editor.document.getText() : "";
      const funcName = await pickFunction(text);
      if (!funcName) return;
      const terminal = vscode.window.createTerminal("CiCode");
      terminal.show();
      terminal.sendText(buildRunCmd(INTERPRETER, ciFiles, funcName));
    }),
  );

  // F5 debug config provider for Python interpreter (cicode-interpreter type)
  cmds.push(
    vscode.debug.registerDebugConfigurationProvider("cicode-interpreter", {
      async resolveDebugConfiguration(
        folder: vscode.WorkspaceFolder | undefined,
        config: vscode.DebugConfiguration,
      ): Promise<vscode.DebugConfiguration | undefined> {
        if (!(await checkPrerequisites())) return undefined;
        await vscode.workspace.saveAll(false);

        // No launch.json — build defaults
        if (!config.type && !config.request && !config.name) {
          const editor = vscode.window.activeTextEditor;
          if (!editor) return undefined;
          const wsRoot =
            folder?.uri.fsPath || path.dirname(editor.document.fileName);
          const ciFiles = fs
            .readdirSync(wsRoot)
            .filter((f) => f.endsWith(".ci"));
          const funcName = await pickFunction(editor.document.getText());
          if (!funcName) return undefined;
          return {
            type: "cicode-interpreter",
            request: "launch",
            name: "CiCode Debug",
            program: editor.document.fileName,
            function: funcName,
            additionalFiles: ciFiles
              .filter(
                (f) =>
                  f !== path.basename(editor.document.fileName),
              )
              .map((f) => path.join(wsRoot, f)),
          };
        }

        if (!config.function) {
          const editor = vscode.window.activeTextEditor;
          const text = editor ? editor.document.getText() : "";
          config.function = await pickFunction(text);
        }
        return config;
      },
    }),
  );

  // F5 debug adapter factory — uses the Python debug_adapter.py
  cmds.push(
    vscode.debug.registerDebugAdapterDescriptorFactory("cicode-interpreter", {
      createDebugAdapterDescriptor(
        _session: vscode.DebugSession,
      ): vscode.DebugAdapterExecutable {
        return new vscode.DebugAdapterExecutable(python, [DEBUG_ADAPTER]);
      },
    }),
  );

  context.subscriptions.push(...cmds);
  return cmds;
}
