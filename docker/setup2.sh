#!/usr/bin/env bash
set -euxo pipefail
cd `dirname "$0"`/..

# create a non-root user for us to run as
groupadd -r nidfuser --gid=999
useradd -r -g nidfuser --uid=999 --home-dir=/workspace --shell=/bin/bash nidfuser
chown -R nidfuser:nidfuser /workspace

# ideally we could lazy-init the files needed to run the official NatCap
# samples through our model. Doing that needs root access to write files to the
# expected locations so in theory doing a setuid on this script should allow
# our non-root user to run the script. That doesn't work in practice. So we'll
# just run it as part of the build.
bash ./docker/prep-for-sample-data-run.sh
