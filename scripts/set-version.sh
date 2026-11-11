#!/usr/bin/env bash
# Sets the package version in apm.yml and the marketplace entry, rebuilds the
# Claude plugin bundle in dist/ and regenerates .claude-plugin/marketplace.json.
# Called by semantic-release (@semantic-release/exec prepareCmd).
set -euo pipefail

VERSION="${1:?usage: set-version.sh <version>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Top-level version and the marketplace package version.
sed -i.bak -E "s/^version: .*/version: ${VERSION}/; s/^(      version: ).*/\1${VERSION}/" apm.yml
rm apm.yml.bak

# Build the bundle first: the marketplace source points there, so the version
# check below reads its plugin.json.
"${ROOT}/scripts/build-dist.sh"

apm pack --check-versions
