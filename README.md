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
[pytest-split](https://github.com/jerry-git/pytest-split). If a repo has a
timings file at `tests/.test_durations`, the split is balanced by expected
runtime; otherwise it is balanced by test count only.

To generate the file, call the CI workflow with `store_durations: true`
(ideally from the nightly job, so that slow tests are timed too). Each test
runner then records the timings of the tests it ran, and once all of them pass
the `Merge Test Timings` job publishes a `test_durations` artifact containing a
merged `<repo>/.test_durations` for every repo that was tested. Commit that
file to `tests/.test_durations` in the corresponding repo. Tests missing from
the file are assumed to take the average time, so it only needs refreshing
occasionally.

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

# Set this to record test timings into build/results/ (see "Test timings")
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
