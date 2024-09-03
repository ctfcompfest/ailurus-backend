FROM faishol27/php:php8

RUN apk add --update --no-cache openssh
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

COPY . .
RUN chmod +x /ssh-entrypoint.sh

EXPOSE 22
EXPOSE 80

ENTRYPOINT ["/ssh-entrypoint.sh"]