FROM ubuntu:14.04
MAINTAINER David Whiteside <david@davidwhiteside.com>
RUN apt-get update
RUN apt-get install -y python \
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
COPY ./docker-entrypoint.sh /
RUN chmod 755 /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
