#!/bin/bash
set -euxo pipefail
cd `dirname "$0"`/..

targetDirs="natcap_invest_docker_flask reveg_alg tests"

# stop the build if there are Python syntax errors or undefined names
flake8 $(echo $targetDirs) --count --select=E9,F63,F7,F82 --show-source \
  --statistics

# exit-zero treats all errors as warnings.
flake8 $(echo $targetDirs) --count --exit-zero --max-complexity=10 --statistics
