#!/bin/sh

# This script must be executed from the $UNIVERSE_HOME directory
# e.g., sh ./scripts/cleanup_datasets/purge_histories.sh

. ./scripts/get_python.sh
. ./setup_paths.sh

$GALAXY_PYTHON ./scripts/cleanup_datasets/cleanup_datasets.py ./universe_wsgi.ini -d 10 -4 -r $@ >> ./scripts/cleanup_datasets/purge_histories.log
