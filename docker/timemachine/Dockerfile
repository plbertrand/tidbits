FROM docker.io/mbentley/timemachine:smb
LABEL maintainer="Pierre-Luc Bertrand <bertrand.pierreluc@gmail.com>"
LABEL version="1.0"
LABEL description="Docker image for Time Machine backups using Zerotier"

RUN apk add --no-cache zerotier-one

EXPOSE 9993/udp

COPY s6/zerotier-one /etc/s6/zerotier-one

ENTRYPOINT ["/entrypoint.sh"]
CMD ["s6-svscan","/etc/s6"]

