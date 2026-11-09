#!/bin/sh
set -eu

runtime_dir=/run/app-secrets
install -d -o app -g app -m 0500 "$runtime_dir"

copy_secret() {
  source_path="$1"
  variable_name="$2"
  target_name="$3"
  if [ -n "$source_path" ]; then
    target_path="$runtime_dir/$target_name"
    install -o app -g app -m 0400 "$source_path" "$target_path"
    export "$variable_name=$target_path"
  fi
}

copy_secret "${DATABASE_PASSWORD_FILE:-}" DATABASE_PASSWORD_FILE postgres_password
copy_secret "${JWT_SECRET_FILE:-}" JWT_SECRET_FILE jwt_secret
copy_secret "${ADMIN_BOOTSTRAP_TOKEN_FILE:-}" ADMIN_BOOTSTRAP_TOKEN_FILE admin_bootstrap_token
copy_secret "${GOOGLE_SERVICE_ACCOUNT_FILE:-}" GOOGLE_SERVICE_ACCOUNT_FILE google_service_account.json

exec gosu app "$@"
