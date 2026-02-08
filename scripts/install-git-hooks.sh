#!/usr/bin/env bash
set -euo pipefail

HOOKS_DIR=".githooks"
TARGET_DIR=".git/hooks"

if [ ! -d "$TARGET_DIR" ]; then
  echo "This repository does not appear to have a .git directory. Run this inside the repository root."
  exit 1
fi

if [ ! -d "$HOOKS_DIR" ]; then
  echo "No $HOOKS_DIR directory found."
  exit 1
fi

echo "Installing git hooks from $HOOKS_DIR to $TARGET_DIR"

for f in "$HOOKS_DIR"/*; do
  name=$(basename "$f")
  target="$TARGET_DIR/$name"
  if [ -f "$target" ]; then
    echo "Overwriting existing hook: $name"
  fi
  cp "$f" "$target"
  chmod +x "$target"
  echo "Installed $name"
done

echo "Done. Run 'git status' to see staged changes after committing."
