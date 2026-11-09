#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
auth_dir="$project_dir/registry/auth"
output_file="$auth_dir/htpasswd"
temporary_file="$auth_dir/htpasswd.tmp"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to create the registry password file." >&2
  exit 1
fi

read -r -p "Registry username: " registry_user
if [[ -z "$registry_user" || "$registry_user" == *:* ]]; then
  echo "Username must be non-empty and must not contain a colon." >&2
  exit 1
fi

read -r -s -p "Registry password: " registry_password
printf '\n'
if [[ ${#registry_password} -lt 16 ]]; then
  echo "Use a password of at least 16 characters." >&2
  exit 1
fi

mkdir -p "$auth_dir"
trap 'rm -f "$temporary_file"' EXIT
printf '%s\n' "$registry_password" |
  docker run --rm -i --entrypoint htpasswd httpd:2 -B -n -i "$registry_user" > "$temporary_file"
chmod 600 "$temporary_file"
mv "$temporary_file" "$output_file"
unset registry_password
trap - EXIT
echo "Registry credentials saved in registry/auth/htpasswd (ignored by Git)."
