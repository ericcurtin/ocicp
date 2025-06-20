#!/bin/bash

main() {
  set -eux -o pipefail 

  find . -name "*.sh" -print0 | xargs -0 shellcheck 
  pylint ocicp
  flake8 ocicp
  black ocicp
}

main "$@"

