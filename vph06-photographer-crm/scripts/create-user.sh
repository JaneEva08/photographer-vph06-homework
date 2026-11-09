#!/usr/bin/env bash
set -euo pipefail

# Assignment-compatible name; keep the implementation in one place.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$script_dir/create-registry-user.sh" "$@"
