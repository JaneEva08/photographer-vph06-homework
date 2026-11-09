#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
secrets_dir="$project_dir/secrets"
mkdir -p "$secrets_dir"
chmod 700 "$secrets_dir"
umask 077

create_random_secret() {
  local destination="$1"
  if [[ ! -s "$destination" ]]; then
    openssl rand -hex 32 > "$destination"
    chmod 600 "$destination"
  fi
}

create_random_secret "$secrets_dir/jwt_secret.txt"
create_random_secret "$secrets_dir/admin_bootstrap_token.txt"
echo "VPh06 signing and one-time registration secrets are ready. Existing files were preserved."
echo "To register the first admin, read secrets/admin_bootstrap_token.txt in this private server terminal and paste it once into the registration form. Never include it in screenshots or Git."
