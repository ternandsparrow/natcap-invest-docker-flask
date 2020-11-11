#!/bin/bash
# fixes lint problems
set -euo pipefail
cd `dirname "$0"`/..

which autopep8 &> /dev/null || {
  echo '[ERROR] autopep8 not installed, install it with:'
  echo '  pip install --upgrade autopep8'
  exit 127
}

find \
  natcap_invest_docker_flask reveg_alg tests \
  -type f \
  -name '*.py' | xargs autopep8 --in-place
