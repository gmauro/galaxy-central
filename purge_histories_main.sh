#!/bin/sh

source ./setup_paths.sh

python2.4 ./scripts/cleanup_datasets.py ./universe_wsgi.ini -4 $@ >> ./purge_histories.log
