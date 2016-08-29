FROM debian:stable
MAINTAINER David Whiteside <david@davidwhiteside.com>

# outbit-api dependencies
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

# outbit application user and group
RUN groupadd -r outbit && useradd -r -g outbit outbit

# outbit-api install latest stable
RUN pip install -U outbit
RUN outbit-api-install

# outbit-api install latest unstable
#RUN apt-get install -y git
#RUN mkdir -p /opt/outbit-dev/ && chmod 700 /opt/outbit-dev/ && chown outbit: /opt/outbit-dev/
#WORKDIR /opt/outbit-dev/
#RUN git clone https://github.com/starboarder2001/outbit.git
#WORKDIR /opt/outbit-dev/outbit/
#RUN python setup.py sdist
#RUN pip install "$(ls -trh dist/|tail -1)"
#RUN outbit-api-install

# outbit-api config
RUN echo "---" > /etc/outbit-api.conf
RUN chmod 400 /etc/outbit-api.conf && chown outbit:outbit /etc/outbit-api.conf
RUN echo "encryption_password: \"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)\"" >> /etc/outbit-api.conf
RUN echo "port: 8080" >> /etc/outbit-api.conf
RUN echo "secure: False" >> /etc/outbit-api.conf
RUN echo "server: 127.0.0.1" >> /etc/outbit-api.conf

# SSL Cert
RUN chown outbit: /etc/ssl/certs/outbit*
RUN chmod 440 /etc/ssl/certs/outbit*

# Log file
RUN touch /var/log/outbit.log && chmod 755 /var/log/outbit.log && chown outbit: /var/log/outbit.log

# NGINX SSL Proxy
COPY ./outbit-nginx.conf /etc/nginx/sites-available/outbit
RUN ln -s /etc/nginx/sites-available/outbit /etc/nginx/sites-enabled/outbit

# Entry Point
COPY ./docker-entrypoint.sh /sbin/
RUN chmod 755 /sbin/docker-entrypoint.sh
ENTRYPOINT ["/sbin/docker-entrypoint.sh"]
