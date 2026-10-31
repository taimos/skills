#!/usr/bin/env bash
# Sets the package version in apm.yml.
# Called by semantic-release (@semantic-release/exec prepareCmd).
set -euo pipefail

VERSION="${1:?usage: set-version.sh <version>}"
cd "$(dirname "$0")/.."

sed -i.bak -E "s/^version: .*/version: ${VERSION}/" apm.yml
rm apm.yml.bak
