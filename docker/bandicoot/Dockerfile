FROM debian:stable
MAINTAINER David Whiteside <david@davidwhiteside.com>

# bandicoot-api dependencies
RUN apt-get update && apt-get install -y python \
  python-setuptools \
  python-dev \
  build-essential \
  libffi-dev \
  openssl \
  libssl-dev \
  nginx \
  python-pip
RUN pip install -U pip
RUN pip install -U setuptools

# bandicoot application user and group
RUN groupadd -r bandicoot && useradd -r -g bandicoot bandicoot

# bandicoot-api install latest stable
RUN pip install -U bandicoot
RUN bandicoot-api-install

# bandicoot-api config
RUN echo "---" > /etc/bandicoot-api.conf
RUN chmod 400 /etc/bandicoot-api.conf && chown bandicoot:bandicoot /etc/bandicoot-api.conf
RUN echo "encryption_password: \"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)\"" >> /etc/bandicoot-api.conf
RUN echo "port: 8080" >> /etc/bandicoot-api.conf
RUN echo "secure: False" >> /etc/bandicoot-api.conf
RUN echo "server: 127.0.0.1" >> /etc/bandicoot-api.conf

# SSL Cert
RUN chown bandicoot: /etc/ssl/certs/bandicoot*
RUN chmod 440 /etc/ssl/certs/bandicoot*

# Log file
RUN touch /var/log/bandicoot.log && chmod 755 /var/log/bandicoot.log && chown bandicoot: /var/log/bandicoot.log

# NGINX SSL Proxy
RUN rm -f /etc/nginx/sites-available/default
COPY ./bandicoot-nginx.conf /etc/nginx/sites-available/bandicoot
RUN ln -s /etc/nginx/sites-available/bandicoot /etc/nginx/sites-enabled/bandicoot

# Entry Point
COPY ./docker-entrypoint.sh /sbin/
RUN chmod 755 /sbin/docker-entrypoint.sh
ENTRYPOINT ["/sbin/docker-entrypoint.sh"]
