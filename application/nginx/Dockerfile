FROM debian:buster-slim

WORKDIR /var/www/html
EXPOSE 80 443

##Install Requirements
RUN apt-get update; apt-get -yq install --no-install-recommends \
    nginx 

COPY . .
COPY nginx/site.conf /etc/nginx/sites-enabled/default

CMD ["nginx", "-g", "daemon off; error_log /dev/stdout error;"]