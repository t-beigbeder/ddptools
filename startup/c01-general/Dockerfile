FROM debian:13-slim AS build-stage
ARG OGV=0.13
RUN apt-get update && \
    apt-get install -y virtualenv python3
COPY . /buildd/
WORKDIR /buildd
RUN virtualenv /venvd && \
    /venvd/bin/pip install -r requirements.txt build && \
    /venvd/bin/python -m build -o pip_repo/otvl-general && \
    virtualenv /venv && \
    /venv/bin/pip install -r requirements.txt pip_repo/otvl-general/otvl_general-${OGV}-py3-none-any.whl awscli

FROM debian:13-slim
RUN apt-get update && \
    apt-get install -y python3 && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /usr/local/bin /home/dv-user  && \
    chown -R 2001:2001 /home/dv-user
COPY --from=build-stage /venv /venv

COPY src/shells/entrypoint.sh /usr/local/bin/entrypoint.sh

USER 2001
ENV LANG=en_US.UTF-8
ENV USER=dv-user
ENV HOME=/home/dv-user
ENV SHELL=/bin/bash
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
