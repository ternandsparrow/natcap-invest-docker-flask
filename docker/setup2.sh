#!/usr/bin/env bash
set -euxo pipefail
cd `dirname "$0"`/..

# create a non-root user for us to run as
groupadd -r nidfuser --gid=999
useradd -r -g nidfuser --uid=999 --home-dir=/workspace --shell=/bin/bash nidfuser
chown -R nidfuser:nidfuser /workspace

# grant setuid so our non-root user can affect the files needed to run the
# official NatCap samples through our model.
chmod u+s ./docker/prep-for-sample-data-run.sh
