import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";

let panel: vscode.WebviewPanel | undefined;

export function registerReferencePanel(
  context: vscode.ExtensionContext,
): vscode.Disposable {
  return vscode.commands.registerCommand("cicode.openReference", () => {
    if (panel) {
      panel.reveal(vscode.ViewColumn.Beside);
      return;
    }

    panel = vscode.window.createWebviewPanel(
      "cicodeReference",
      "CiCode Reference",
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true },
    );

    panel.onDidDispose(() => {
      panel = undefined;
    });

    const builtinsPath = context.asAbsolutePath(
      path.join("builtins", "builtinFunctions.json"),
    );

    let functions: Record<string, unknown> = {};
    try {
      const raw = JSON.parse(fs.readFileSync(builtinsPath, "utf8"));
      functions = raw?.functions ?? raw;
    } catch {
      // builtins not available
    }

    panel.webview.html = buildHtml(functions);
  });
}

function buildHtml(functions: Record<string, unknown>): string {
  // Serialise just the fields we need for the panel (keep payload small)
  type Slim = {
    name: string;
    returnType: string;
    params: string[];
    doc: string;
    returns?: string;
    paramDocs?: Record<string, string>;
  };

  const slim: Slim[] = Object.values(functions).map((f: unknown) => {
    const fn = f as {
      name?: string;
      returnType?: string;
      params?: string[];
      doc?: string;
      returns?: string;
      paramDocs?: Record<string, string>;
    };
    return {
      name: fn.name ?? "",
      returnType: fn.returnType ?? "UNKNOWN",
      params: fn.params ?? [],
      doc: fn.doc ?? "",
      returns: fn.returns,
      paramDocs: fn.paramDocs,
    };
  });

  const json = JSON.stringify(slim);

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CiCode Reference</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size);
    color: var(--vscode-foreground);
    background: var(--vscode-editor-background);
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  #search-bar {
    padding: 8px 12px;
    border-bottom: 1px solid var(--vscode-panel-border, #444);
    background: var(--vscode-sideBar-background, var(--vscode-editor-background));
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    gap: 8px;
    align-items: center;
  }
  #search-bar input {
    flex: 1;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    border: 1px solid var(--vscode-input-border, #555);
    padding: 5px 8px;
    border-radius: 3px;
    font-size: inherit;
    font-family: inherit;
    outline: none;
  }
  #search-bar input:focus {
    border-color: var(--vscode-focusBorder, #007fd4);
  }
  #count {
    font-size: 0.8em;
    color: var(--vscode-descriptionForeground);
    white-space: nowrap;
  }
  #layout {
    display: flex;
    flex: 1;
    overflow: hidden;
  }
  #list {
    width: 240px;
    min-width: 140px;
    overflow-y: auto;
    border-right: 1px solid var(--vscode-panel-border, #444);
    background: var(--vscode-sideBar-background, var(--vscode-editor-background));
  }
  .fn-item {
    padding: 6px 12px;
    cursor: pointer;
    border-bottom: 1px solid transparent;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .fn-item:hover {
    background: var(--vscode-list-hoverBackground);
  }
  .fn-item.selected {
    background: var(--vscode-list-activeSelectionBackground);
    color: var(--vscode-list-activeSelectionForeground);
  }
  .fn-name { font-weight: 600; }
  .fn-ret {
    font-size: 0.75em;
    color: var(--vscode-descriptionForeground);
    margin-left: 6px;
  }
  #detail {
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
  }
  #detail h2 {
    font-size: 1.3em;
    color: var(--vscode-textLink-foreground);
    margin-bottom: 8px;
  }
  .sig {
    font-family: var(--vscode-editor-font-family, monospace);
    background: var(--vscode-textCodeBlock-background);
    padding: 8px 12px;
    border-radius: 4px;
    margin-bottom: 12px;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .section {
    font-weight: bold;
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--vscode-textPreformat-foreground);
    margin: 14px 0 4px;
  }
  p.doc { line-height: 1.6; }
  table { border-collapse: collapse; width: 100%; margin-top: 4px; }
  td { padding: 4px 8px; border-bottom: 1px solid var(--vscode-panel-border, #444); vertical-align: top; }
  td.p { font-family: var(--vscode-editor-font-family, monospace); white-space: nowrap; min-width: 130px; color: var(--vscode-textLink-foreground); }
  .empty { color: var(--vscode-descriptionForeground); padding: 12px; font-style: italic; }
</style>
</head>
<body>
<div id="search-bar">
  <input id="q" type="text" placeholder="Search functions…" autofocus>
  <span id="count"></span>
</div>
<div id="layout">
  <div id="list"></div>
  <div id="detail"><p class="empty">Select a function to view its documentation.</p></div>
</div>
<script>
const ALL = ${json};
ALL.sort((a, b) => a.name.localeCompare(b.name));

const listEl = document.getElementById('list');
const detailEl = document.getElementById('detail');
const qEl = document.getElementById('q');
const countEl = document.getElementById('count');

let filtered = ALL.slice();
let selectedName = null;

function esc(s) {
  return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderList() {
  listEl.innerHTML = '';
  if (filtered.length === 0) {
    listEl.innerHTML = '<p class="empty">No matches.</p>';
    countEl.textContent = '0 / ' + ALL.length;
    return;
  }
  countEl.textContent = filtered.length + ' / ' + ALL.length;
  filtered.forEach(fn => {
    const div = document.createElement('div');
    div.className = 'fn-item' + (fn.name === selectedName ? ' selected' : '');
    div.dataset.name = fn.name;
    div.innerHTML = '<span class="fn-name">' + esc(fn.name) + '</span><span class="fn-ret">' + esc(fn.returnType) + '</span>';
    div.addEventListener('click', () => showDetail(fn));
    listEl.appendChild(div);
  });
}

function showDetail(fn) {
  selectedName = fn.name;
  document.querySelectorAll('.fn-item').forEach(el => {
    el.classList.toggle('selected', el.dataset.name === fn.name);
  });

  const sig = fn.name + '(' + fn.params.join(', ') + ')';
  const paramRows = fn.params.map(p => {
    const doc = fn.paramDocs && fn.paramDocs[p] ? fn.paramDocs[p] : '';
    return '<tr><td class="p">' + esc(p) + '</td><td>' + esc(doc) + '</td></tr>';
  }).join('');

  detailEl.innerHTML =
    '<h2>' + esc(fn.name) + '</h2>' +
    '<div class="sig">' + esc(sig) + '</div>' +
    (fn.doc ? '<p class="doc">' + esc(fn.doc) + '</p>' : '') +
    '<div class="section">Return Value</div>' +
    '<p>' + esc(fn.returnType) + (fn.returns ? ' — ' + esc(fn.returns) : '') + '</p>' +
    (paramRows ? '<div class="section">Parameters</div><table>' + paramRows + '</table>' : '');
}

qEl.addEventListener('input', () => {
  const q = qEl.value.trim().toLowerCase();
  filtered = q
    ? ALL.filter(fn => fn.name.toLowerCase().includes(q) || fn.doc.toLowerCase().includes(q))
    : ALL.slice();
  renderList();
});

renderList();
countEl.textContent = ALL.length + ' / ' + ALL.length;
</script>
</body>
</html>`;
}
