#!/bin/bash

available() {
  command -v "$1" >/dev/null
}

main() {
  set -e -o pipefail

  local bin="ocicp"
  if ! available "skopeo"; then
    echo "Error: $bin requires skopeo to complete installation."

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

  local url="https://raw.githubusercontent.com/ericcurtin/$bin/refs/heads/main/$bin"
  curl -fsSL "$url" -o "$dir/$bin"
  chmod a+rx "$dir/$bin"
}

main "$@"
