import * as vscode from "vscode";
import type { Rule } from "../rule";
import type { CheckContext } from "../context";
import { diag } from "../diag";
import { inSpan } from "../../../shared/textUtils";
import { BLOCK_START_KEYWORDS } from "../../../shared/constants";

/**
 * Searches forward from `startPos` for `keyword` respecting
 * parenthesis depth and stopping at statement boundaries.
 */
const THEN_RE = /^THEN\b/i;
const DO_RE = /^DO\b/i;

function findKeywordAfter(
  text: string,
  ignoreNoHeaders: Array<[number, number]>,
  startPos: number,
  keywordRe: RegExp,
  maxRange: number,
): boolean {
  let searchPos = startPos;
  let parenDepth = 0;
  const maxSearch = Math.min(startPos + maxRange, text.length);

  while (searchPos < maxSearch) {
    if (inSpan(searchPos, ignoreNoHeaders)) {
      searchPos++;
      continue;
    }

    const ch = text[searchPos];

    if (ch === "(") {
      parenDepth++;
      searchPos++;
      continue;
    } else if (ch === ")") {
      parenDepth--;
      searchPos++;
      continue;
    }

    if (parenDepth === 0) {
      const prevChar = searchPos > 0 ? text[searchPos - 1] : " ";
      if (!/[A-Za-z0-9_]/.test(prevChar)) {
        const slice = text.slice(searchPos, searchPos + 10);
        if (keywordRe.test(slice)) return true;

        const wordMatch = /^([A-Za-z]+)\b/.exec(
          text.slice(searchPos, searchPos + 10),
        );
        if (wordMatch) {
          const w = wordMatch[1].toUpperCase();
          if (w === "END" || BLOCK_START_KEYWORDS.has(w)) return false;
        }
      }
    }

    searchPos++;
  }

  return false;
}

/**
 * Checks that:
 * - E2032: every IF has a matching THEN
 * - E2033: every WHILE has a matching DO
 */
export const controlFlowRule: Rule = {
  id: "controlFlow",

  check({
    text,
    ignore,
    ignoreNoHeaders,
    doc,
    diagnosticsEnabled,
  }: CheckContext): vscode.Diagnostic[] {
    if (!diagnosticsEnabled) return [];

    const diags: vscode.Diagnostic[] = [];

    const ifRe = /\bIF\b/gi;
    let m: RegExpExecArray | null;

    while ((m = ifRe.exec(text))) {
      if (inSpan(m.index, ignoreNoHeaders)) continue;
      if (inSpan(m.index, ignore)) continue;

      if (
        !findKeywordAfter(text, ignoreNoHeaders, m.index + 2, THEN_RE, 10000)
      ) {
        const pos = doc.positionAt(m.index);
        diags.push(
          diag(
            new vscode.Range(pos, pos.translate(0, 2)),
            "IF statement requires THEN keyword.",
            vscode.DiagnosticSeverity.Error,
            "E2032",
          ),
        );
      }
    }

    const whileRe = /\bWHILE\b/gi;
    while ((m = whileRe.exec(text))) {
      if (inSpan(m.index, ignoreNoHeaders)) continue;
      if (inSpan(m.index, ignore)) continue;

      if (!findKeywordAfter(text, ignoreNoHeaders, m.index + 5, DO_RE, 10000)) {
        const pos = doc.positionAt(m.index);
        diags.push(
          diag(
            new vscode.Range(pos, pos.translate(0, 5)),
            "WHILE statement requires DO keyword.",
            vscode.DiagnosticSeverity.Error,
            "E2033",
          ),
        );
      }
    }

    // Detect run-on keywords at statement start: "WHILEvar", "SELECTvar", "RETURNvar",
    // "IFvar", "FORvar" — keyword glued to identifier due to missing space.
    // Only flag at statement-start positions (start of line after whitespace, or after ;)
    // to avoid false positives inside expressions or comments.
    // NOTE: NO 'i' flag — keywords must be uppercase to avoid false-positives on
    // legitimate function names like FormNew, FormPrompt, FormulaEditorFormulaList.
    const RUNON_RE =
      /(?:^|;)\s*\b((WHILE|SELECT|RETURN|IF|FOR)([A-Za-z_][A-Za-z0-9_]*))\b/gm;
    while ((m = RUNON_RE.exec(text))) {
      // m[1] = full token (e.g. "WHILEznRow"), m[2] = keyword, m[3] = suffix
      const fullToken = m[1];
      const keyword = m[2].toUpperCase();
      const rest = m[3];
      // Position of fullToken within the line
      const tokenIndex = m.index + m[0].length - fullToken.length;
      if (inSpan(tokenIndex, ignoreNoHeaders)) continue;
      if (inSpan(tokenIndex, ignore)) continue;
      const pos = doc.positionAt(tokenIndex);
      diags.push(
        diag(
          new vscode.Range(pos, pos.translate(0, fullToken.length)),
          `'${fullToken}' is not a valid keyword — missing space? Did you mean '${keyword} ${rest}'?`,
          vscode.DiagnosticSeverity.Error,
          "E2041",
        ),
      );
    }

    return diags;
  },
};
