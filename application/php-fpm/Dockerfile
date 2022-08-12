FROM debian:buster-slim

WORKDIR /app
EXPOSE 9000 443

#Install Requirements
RUN apt-get update; apt-get -yq install --no-install-recommends \
    php php-fpm php-common php-pdo php-mysql php-mbstring php-curl

RUN mkdir /run/php

# support for php-fpm to read env vars
RUN sed -r -i 's/^\;(clear_env = )(.*)/\1 no/' /etc/php/7.3/fpm/pool.d/www.conf
# enable localhost listening
RUN sed -i -e '/listen =/ s/= .*/= 127\.0\.0\.1\:9000/' /etc/php/7.3/fpm/pool.d/www.conf

COPY . /app
 
CMD ["/usr/sbin/php-fpm7.3", "-F"]