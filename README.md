# ci-settings

This is our repo containing the docker image used for our CI. Most people
won't need to touch this, and instead should use our regular images. This is
mostly useful if you are either hacking on CI, or super confused why tests are
failing for your pull request.

## CI options
Other PRs can be used in place of default branches by simply linking the PR, for example
```
sync: angr/angr#<id>
```

## Test timings

Tests are split across the test runners with
[pytest-split](https://github.com/jerry-git/pytest-split), balanced by how
long each test took in earlier runs. Nothing needs to be committed: the
timings live in the GitHub Actions cache of the repo being tested.

Runs on the default branch record the timings of the tests they ran and, if
all test runners pass, the `Save Test Timings` job merges them into the
previously cached timings and saves the result as a new `test-durations-*`
cache entry. Every run, including pull requests, restores the most recent
entry. Tests without a recorded timing are assumed to take the average time,
and with no cache entry at all the split is balanced by test count only.

To start over, delete the `test-durations-*` entries from the repo's Actions
caches.

## Manual instructions

To perform a build manually:

```sh
docker run -it \
    --cap-add=SYS_PTRACE \
    --security-opt seccomp:unconfined \
    -v /var/run/docker.sock:/var/run/docker.sock \  # for archr
    angr/ci:2
```

And then, in the container:

```sh
# This script will put you in the same directory as Azure would. It also sets
# all the necessary environment variables.
source /root/scripts/manual_defaults.sh

# OPTIONAL: If you need to customize environment variables, these are the
# important ones, along with their default values.

# Change these to the relevant repo and branch
# Your pull request will be refs/pull/{id}
export GITHUB_REPOSITORY=angr/angr
export GITHUB_REF=refs/heads/master

# We slice up our test execution among workers, 10 currently. You can play with
# these # numbers to run only a subset of the tests. You can change these
# between running the ga-test.sh script, without rebuilding.
export WORKER=0
export NUM_WORKERS=10

# Test timings (see "Test timings"). Timings in TEST_DURATIONS_DIR are used to
# balance the split, and STORE_DURATIONS records new ones into build/results/.
export TEST_DURATIONS_DIR=$PWD/test_durations
export STORE_DURATIONS=false

# And finally, to run the individual steps:

# Build step
/root/scripts/ga-build.sh
# Lint step
/root/scripts/ga-lint.sh
# Test step
/root/scripts/ga-test.sh
```

After building, there will be a `build` directory you can `cd` into that has
everything of interest. Most importantly, the `virtualenv` and `src` directories
you can use if you need to run specific tests outside of the standard testing
scripts.
