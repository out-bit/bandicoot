FROM ubuntu:14.04
MAINTAINER David Whiteside <david@davidwhiteside.com>
RUN apt-get update && apt-get install -y python \
  python-setuptools \
  python-dev \
  build-essential \
  libffi-dev \
  openssl \
  libssl-dev
RUN easy_install pip
RUN pip install -U pip
RUN pip install outbit
RUN pip install -U setuptools
RUN outbit-api-install
RUN groupadd -r outbit && useradd -r -g outbit outbit
RUN echo "---" > /etc/outbit-api.conf
RUN chmod 400 /etc/outbit-api.conf && chown outbit /etc/outbit-api.conf && chgrp outbit /etc/outbit-api.conf
RUN echo "encryption_password: \"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)\"" >> /etc/outbit-api.conf
COPY ./docker-entrypoint.sh /
RUN chmod 755 /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
