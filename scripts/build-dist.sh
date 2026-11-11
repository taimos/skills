#!/usr/bin/env bash
# Builds the Claude plugin bundle into dist/taimos-skills/.
# .claude-plugin/marketplace.json points to this bundle, so Claude Code, Claude
# Desktop and claude.ai get native skills/ from a plain marketplace install.
# Called by set-version.sh during the release; CI calls it with a temp dir.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-${ROOT}/dist}"
NAME="taimos-skills"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

mkdir -p "${OUT}"

# apm install deploys into harness folders next to apm.yml, so pack from a
# scratch copy and never from the source tree.
mkdir "${WORK}/pkg"
tar -C "${ROOT}" --exclude=./.git --exclude=./dist --exclude=./apm_modules \
  --exclude=./.claude-plugin --exclude=./.github/plugin -cf - . \
  | tar -C "${WORK}/pkg" -xf -
(cd "${WORK}/pkg" && apm install && apm pack --format claude-plugin -o "${WORK}/out")

bundle="$(find "${WORK}/out" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
rm -rf "${OUT:?}/${NAME}"
mv "${bundle}" "${OUT}/${NAME}"

# Claude Desktop and claude.ai expect the manifest under .claude-plugin/.
mkdir -p "${OUT}/${NAME}/.claude-plugin"
mv "${OUT}/${NAME}/plugin.json" "${OUT}/${NAME}/.claude-plugin/plugin.json"
