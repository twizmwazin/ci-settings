#!/bin/bash -ex

BASEDIR=$(dirname $(dirname $0))
SCRIPTS=$BASEDIR/scripts
CONF=$BASEDIR/conf


# Test timings restored from the Actions cache, if any
export TEST_DURATIONS_DIR=${TEST_DURATIONS_DIR:-$PWD/test_durations}

tar -I zstd -xf build.tar.zst
cd build

source virtualenv/bin/activate

$SCRIPTS/test.py $REPO_NAME
