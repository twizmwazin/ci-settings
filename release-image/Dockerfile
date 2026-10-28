FROM ubuntu:24.04

RUN apt-get update \
    && apt-get -o APT::Immediate-Configure=0 install -y python3-dev python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -s /bin/bash -m angr
USER angr
WORKDIR /home/angr

RUN python3 -m venv --prompt angr .venv
RUN echo "source /home/angr/.venv/bin/activate" >> /home/angr/.bashrc
# setuptools required for capstone with python 3.12
RUN /home/angr/.venv/bin/pip install -U pip setuptools

# packages/ holds the wheels and sdists built by the release pipeline, so the
# image can be built before the release reaches PyPI. Anything not found there
# is installed from PyPI.
ARG ANGR_VERSION
RUN --mount=type=bind,source=packages,target=/tmp/packages \
    /home/angr/.venv/bin/pip install --no-cache-dir --find-links /tmp/packages "angr[angrdb,unicorn]==${ANGR_VERSION}"
