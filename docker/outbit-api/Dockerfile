FROM debian:stable
MAINTAINER David Whiteside <david@davidwhiteside.com>

# outbit-api installation
RUN apt-get update && apt-get install -y python \
  python-setuptools \
  python-dev \
  build-essential \
  libffi-dev \
  openssl \
  libssl-dev \
  python-pip
RUN pip install -U pip
RUN pip install -U setuptools
RUN pip install outbit
RUN outbit-api-install

# outbit application user and group
RUN groupadd -r outbit && useradd -r -g outbit outbit

# outbit-api config
RUN echo "---" > /etc/outbit-api.conf
RUN chmod 400 /etc/outbit-api.conf && chown outbit:outbit /etc/outbit-api.conf
RUN echo "encryption_password: \"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)\"" >> /etc/outbit-api.conf
RUN echo "secure: True" >> /etc/outbit-api.conf
RUN echo "ssl_key: /etc/ssl/localcerts/outbit.com.key" >> /etc/outbit-api.conf
RUN echo "ssl_crt: /etc/ssl/localcerts/outbit.com.crt" >> /etc/outbit-api.conf

# SSL Cert Generation
COPY ./gencert.sh /sbin/
RUN chown root:root /sbin/gencert.sh && chmod 700 /sbin/gencert.sh
RUN mkdir -p /etc/ssl/localcerts/ && chmod 700 /etc/ssl/localcerts/ && chown outbit: /etc/ssl/localcerts/
WORKDIR /etc/ssl/localcerts/
RUN /sbin/gencert.sh outbit.com
RUN chown outbit: /etc/ssl/localcerts/outbit.com*

# Log file
RUN touch /var/log/outbit.log && chmod 755 /var/log/outbit.log && chown outbit: /var/log/outbit.log

# Entry Point
COPY ./docker-entrypoint.sh /sbin/
RUN chmod 755 /sbin/docker-entrypoint.sh
ENTRYPOINT ["/sbin/docker-entrypoint.sh"]
