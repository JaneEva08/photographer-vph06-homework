#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
secrets_dir="$project_dir/secrets"
mkdir -p "$secrets_dir"
chmod 700 "$secrets_dir"
umask 077

write_secret() {
  local label="$1"
  local destination="$2"
  local value

  read -r -s -p "$label (at least 16 characters): " value
  printf '\n'
  if [[ ${#value} -lt 16 ]]; then
    echo "$label must contain at least 16 characters." >&2
    unset value
    return 1
  fi

  printf '%s' "$value" > "$destination"
  chmod 600 "$destination"
  unset value
}

write_secret "PostgreSQL password" "$secrets_dir/postgres_password.txt"
write_secret "pgAdmin password" "$secrets_dir/pgadmin_password.txt"
echo "Local secret files created. This directory is ignored by Git."
