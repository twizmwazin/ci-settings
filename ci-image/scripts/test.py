#!/usr/bin/env python3

import json
import os
import subprocess
import sys

from repos import Target, load_config


GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "angr/angr")
REPO = GITHUB_REPOSITORY.split("/")[-1]
NUM_WORKERS = os.environ.get("NUM_WORKERS", 1)
# Adjust WORKER to be 1-indexed for pytest-split
WORKER = int(os.environ.get("WORKER", 0)) + 1
NIGHTLY = os.environ.get("NIGHTLY", "false").lower() == "true"
INCLUDE_SELF = os.environ.get("INCLUDE_SELF", "true").lower() == "true"
STORE_DURATIONS = os.environ.get("STORE_DURATIONS", "false").lower() == "true"

# Name of the pytest-split timings file, looked up in each project's tests directory
DURATIONS_FILE = ".test_durations"
RESULTS_DIR = "results"


def load_durations(path: str) -> dict[str, float]:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def test_project(project: str) -> bool:
    command = (
        f"pytest -v -nauto --forked --splits {NUM_WORKERS} --group {WORKER} "
        f"--rootdir=./src/{project}/tests ./src/{project}/tests"
    )

    # If the project ships a timings file, use it to balance the groups by
    # expected runtime. Without one, pytest-split falls back to splitting by
    # test count.
    durations_path = f"./src/{project}/tests/{DURATIONS_FILE}"
    known_durations = load_durations(durations_path)
    if known_durations:
        print(f"Using test timings from {durations_path}", flush=True)
        command += " --splitting-algorithm least_duration"
    else:
        print(f"No test timings found at {durations_path}", flush=True)

    stored_path = None
    if STORE_DURATIONS:
        # pytest-split reads and writes the same file, so record into a copy.
        # The copy is seeded with the known timings so that this run is still
        # split the same way as every other worker's.
        os.makedirs(RESULTS_DIR, exist_ok=True)
        stored_path = f"{RESULTS_DIR}/{project}.{WORKER}.durations.json"
        with open(stored_path, "w") as f:
            json.dump(known_durations, f)
        durations_path = stored_path
        command += " --store-durations"

    if known_durations or STORE_DURATIONS:
        command += f" --durations-path {durations_path}"

    if not NIGHTLY:
        command += ' -m "not slow"'

    print(f"Running test command:\n{command}", flush=True)
    rc = subprocess.run(command, shell=True).returncode

    if stored_path is not None:
        # Keep only the tests this worker actually ran, so that merging the
        # files from all workers yields a timings file without stale entries.
        measured = {
            test: duration
            for test, duration in load_durations(stored_path).items()
            if known_durations.get(test) != duration
        }
        with open(stored_path, "w") as f:
            json.dump(measured, f, sort_keys=True, indent=4)

    if rc not in (0, 5):
        print(f"Tests failed for {project} with return code {rc}", flush=True)
        return False
    else:
        print(f"Tests passed for {project}", flush=True)
        return True


def build_reverse_deps(targets: list[Target]) -> dict[str, set[str]]:
    reverse_deps: dict[str, set[str]] = {}
    for t in targets:
        for dep in t.deps:
            reverse_deps.setdefault(dep, set()).add(t.repo)
    return reverse_deps


def collect_all_dependents(repo: str, reverse_deps: dict[str, set[str]]) -> set[str]:
    result: set[str] = set()
    stack = [repo]
    while stack:
        current = stack.pop()
        for dep in reverse_deps.get(current, []):
            if dep not in result:
                result.add(dep)
                stack.append(dep)
    return result


def main():
    targets: list[Target] = load_config("/root/conf/repo-list.txt")

    if NIGHTLY:
        repos_to_test = [REPO]
    else:
        reverse_deps = build_reverse_deps(targets)
        repo_dependents = collect_all_dependents(REPO, reverse_deps)
        if INCLUDE_SELF:
            repo_dependents.add(REPO)
        repos_to_test = sorted(repo_dependents)

    fail_count = 0
    for repo in repos_to_test:
        fail_count += int(not test_project(repo))

    sys.exit(fail_count)


if __name__ == "__main__":
    main()
