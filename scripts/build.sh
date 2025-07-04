#!/bin/bash

main() {
  set -ex -o pipefail

  if [ "$1" == "install" ]; then
    sudo apt install -y pylint black flake8
  fi

  find . -name "*.sh" -print0 | xargs -0 shellcheck 

  black --line-length 80 ocicp
  flake8 --max-line-length 80 ocicp
  pylint --disable=missing-function-docstring ocicp
}

main "$@"

