FROM python:3.13-slim as build
WORKDIR /src
COPY requirements.txt /src/
RUN python -m venv /venv && \
 /venv/bin/pip install -r requirements.txt

FROM debpy:1
COPY otvl_general /src/otvl_general
RUN mkdir -p /home/dv-user  && \
    chown -R 2001:2001 /home/dv-user

USER 2001
WORKDIR /home/dv-user
COPY --from=build /venv /venv
ENV LANG=en_US.UTF-8
ENV USER=dv-user
ENV HOME=/home/dv-user
ENV SHELL=/bin/bash
ENV PYTHONPATH=/src
