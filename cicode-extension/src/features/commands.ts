import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import type { Indexer } from "../core/indexer/indexer";
import { rebuildBuiltins, resolveContentPath } from "../core/builtins/builtins";
import { insertDocSkeletonAtCursor } from "./docSkeleton";
import type { FunctionInfo } from "../shared/types";

export function registerCommands(
  context: vscode.ExtensionContext,
  indexer: Indexer,
  cfg: () => vscode.WorkspaceConfiguration,
): vscode.Disposable[] {
  const cmds: vscode.Disposable[] = [];

  cmds.push(
    vscode.commands.registerCommand("cicode.rebuildBuiltins", async () => {
      await rebuildBuiltins(context, cfg);
      await indexer.buildAll();
      vscode.window.showInformationMessage("Cicode: rebuilt builtin cache.");
    }),
  );

  cmds.push(
    vscode.commands.registerCommand("cicode.reindexAll", async () => {
      await indexer.buildAll();
      vscode.window.showInformationMessage("Cicode: full reindex complete.");
    }),
  );

  cmds.push(
    vscode.commands.registerCommand(
      "cicode.openHelpForSymbol",
      async (symbol?: string) => {
        const editor = vscode.window.activeTextEditor;
        if (!symbol && !editor) return;

        const name =
          symbol ||
          editor!.document.getText(
            editor!.document.getWordRangeAtPosition(
              editor!.selection.active,
              /\w+/,
            ),
          );

        const f = indexer.getAllFunctions().get(name.toLowerCase());

        if (!f) {
          vscode.window.showInformationMessage(`No help found for '${name}'.`);
          return;
        }

        // Try to open AVEVA HTML help file if the user has AVEVA installed
        const contentPath = resolveContentPath(cfg);
        if (contentPath && f.helpPath) {
          const fullPath = path.join(contentPath, f.helpPath);
          if (fs.existsSync(fullPath)) {
            await vscode.env.openExternal(vscode.Uri.file(fullPath));
            return;
          }
        }

        // Fallback: show built-in docs in a WebView panel
        showBuiltinHelpPanel(context, f);
      },
    ),
  );

  cmds.push(
    vscode.commands.registerCommand("cicode.insertDocSkeleton", async () => {
      const ok = await insertDocSkeletonAtCursor(indexer);
      if (ok)
        vscode.window.showInformationMessage("Cicode: Inserted doc skeleton.");
    }),
  );

  cmds.push(
    vscode.commands.registerCommand("cicode.addSpaceIfNeeded", async () => {
      const ed = vscode.window.activeTextEditor;
      if (!ed) return;

      const doc = ed.document;
      const isStopper = (ch: string) =>
        ch === " " ||
        ch === ";" ||
        ch === "," ||
        ch === ")" ||
        ch === "]" ||
        ch === "}" ||
        ch === "\t";
      const isIdent = (ch: string) => /[A-Za-z0-9_]/.test(ch);

      await ed.edit((eb) => {
        for (const sel of ed.selections) {
          const pos = sel.active;
          if (!sel.isEmpty) continue;

          const lineText = doc.lineAt(pos.line).text;
          const nextCh =
            pos.character < lineText.length ? lineText[pos.character] : "";
          const prevCh = pos.character > 0 ? lineText[pos.character - 1] : "";
          if (isStopper(nextCh) || prevCh === " ") continue;
          if (isIdent(nextCh)) continue;

          eb.insert(pos, " ");
        }
      });
    }),
  );

  cmds.push(
    vscode.commands.registerCommand("cicode.createNewFile", async () => {
      const folder = vscode.workspace.workspaceFolders?.[0];
      if (!folder) {
        return;
      }

      while (true) {
        const fileName = await vscode.window.showInputBox({
          prompt: "Enter new Cicode filename",
        });

        // Return if ESC pressed
        if (fileName === undefined) {
          return;
        }

        // Prompt again if given file name is empty
        if (fileName.trim() === "") {
          vscode.window.showErrorMessage("Empty filename is not allowed");
          continue;
        }

        const fileUri = vscode.Uri.joinPath(folder.uri, fileName);
        try {
          await vscode.workspace.fs.stat(fileUri);
          vscode.window.showErrorMessage(
            `File "${fileName}" already exists. Please input another name.`,
          );
        } catch {
          await vscode.workspace.fs.writeFile(fileUri, new Uint8Array());
          await vscode.window.showTextDocument(fileUri);
          return;
        }
      }
    }),
  );
  context.subscriptions.push(...cmds);
  return cmds;
}

function showBuiltinHelpPanel(
  context: vscode.ExtensionContext,
  f: FunctionInfo,
): void {
  const panel = vscode.window.createWebviewPanel(
    "cicodeHelp",
    `CiCode: ${f.name}`,
    vscode.ViewColumn.Beside,
    { enableScripts: false },
  );

  const signature = `${f.name}(${(f.params ?? []).join(", ")})`;
  const returnType = f.returnType ?? "UNKNOWN";

  const paramRows = (f.params ?? [])
    .map((p) => {
      const doc = f.paramDocs?.[p] ?? "";
      return `<tr><td class="param">${esc(p)}</td><td>${esc(doc)}</td></tr>`;
    })
    .join("\n");

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(f.name)}</title>
<style>
  body { font-family: var(--vscode-font-family); font-size: var(--vscode-font-size); color: var(--vscode-foreground); background: var(--vscode-editor-background); padding: 1.5em 2em; max-width: 800px; }
  h1 { font-size: 1.4em; margin-bottom: 0.2em; color: var(--vscode-textLink-foreground); }
  .signature { font-family: var(--vscode-editor-font-family, monospace); background: var(--vscode-textCodeBlock-background); padding: 0.5em 0.8em; border-radius: 4px; margin: 0.8em 0; font-size: 1em; white-space: pre-wrap; word-break: break-all; }
  .section-title { font-weight: bold; margin-top: 1.2em; margin-bottom: 0.3em; color: var(--vscode-textPreformat-foreground); text-transform: uppercase; font-size: 0.8em; letter-spacing: 0.05em; }
  p { margin: 0.4em 0; line-height: 1.6; }
  table { border-collapse: collapse; width: 100%; margin-top: 0.4em; }
  td { padding: 0.35em 0.6em; border-bottom: 1px solid var(--vscode-panel-border, #444); vertical-align: top; }
  td.param { font-family: var(--vscode-editor-font-family, monospace); white-space: nowrap; min-width: 140px; color: var(--vscode-textLink-foreground); }
  .return-type { font-family: var(--vscode-editor-font-family, monospace); color: var(--vscode-textLink-activeForeground); }
  .offline-note { font-size: 0.8em; color: var(--vscode-descriptionForeground); margin-top: 2em; border-top: 1px solid var(--vscode-panel-border, #444); padding-top: 0.6em; }
</style>
</head>
<body>
<h1>${esc(f.name)}</h1>
<div class="signature">${esc(signature)}</div>
${f.doc ? `<p>${esc(f.doc)}</p>` : ""}
${f.returns ? `<div class="section-title">Return Value</div><p><span class="return-type">${esc(returnType)}</span> — ${esc(f.returns)}</p>` : `<div class="section-title">Return Type</div><p class="return-type">${esc(returnType)}</p>`}
${paramRows ? `<div class="section-title">Parameters</div><table>${paramRows}</table>` : ""}
<p class="offline-note">Offline reference — set <code>cicode.avevaPath</code> to your AVEVA install for full HTML help.</p>
</body>
</html>`;

  panel.webview.html = html;
}

function esc(s: string | undefined): string {
  return (s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
