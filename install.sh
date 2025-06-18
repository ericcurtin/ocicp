#!/bin/bash

available() {
  command -v "$1" >/dev/null
}

main() {
  set -e -o pipefail

  if ! available "skopeo"; then
    echo "Error: ocicp requires skopeo to complete installation."

    return 1
  fi

  IFS=":"
  for dir in $PATH; do
    if [ -d "$dir" ] && [ -w "$dir" ]; then
      break
    fi
  done

  if [ -z "$dir" ]; then
    echo "Error: No writable directory found in \$PATH."
    echo "Please run as a user (sudo) with write permissions to a directory in \$PATH."

    return 1
  fi

  local f="ocicp"
  local url="https://raw.githubusercontent.com/ericcurtin/ocicp/refs/heads/main/$f"
  curl -fsSL "$url" -o "$dir/$f"
  chmod a+rx "$dir/$f"
}

main "$@"
