#!/bin/bash
# build.sh — build and install the CiCode VSCode extension
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXT_DIR="$SCRIPT_DIR/cicode-extension"

echo "→ Syncing interpreter into extension bundle..."
rm -rf "$EXT_DIR/interpreter"
cp -r "$SCRIPT_DIR/interpreter" "$EXT_DIR/interpreter"

echo "→ Packaging VSIX..."
cd "$EXT_DIR"
vsce package --allow-missing-repository --no-dependencies 2>&1 | grep -v "^$"

VSIX=$(ls "$EXT_DIR"/cicode-*.vsix | sort -V | tail -1)
cp "$VSIX" "$SCRIPT_DIR/"

echo "→ Installing extension..."
code --install-extension "$VSIX"

echo ""
echo "✓ Done! Reload VSCode: Ctrl+Shift+P → Developer: Reload Window"
