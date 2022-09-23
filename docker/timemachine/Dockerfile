FROM docker.io/mbentley/timemachine:smb
LABEL maintainer="Pierre-Luc Bertrand <bertrand.pierreluc@gmail.com>"
LABEL version="1.0"
LABEL description="Docker image for Time Machine backups using Zerotier"

RUN apk add --no-cache openrc

#RUN apk add --no-cache zerotier-one
RUN wget https://dl-cdn.alpinelinux.org/alpine/v3.17/community/x86_64/zerotier-one-openrc-1.10.2-r0.apk
RUN wget https://dl-cdn.alpinelinux.org/alpine/v3.17/community/x86_64/zerotier-one-1.10.2-r0.apk
RUN apk add zerotier-one-1.10.2-r0.apk 
RUN apk add zerotier-one-openrc-1.10.2-r0.apk 
RUN rc-update add zerotier-one
#RUN apk add --no-cache --update  fuse-overlayfs
#RUN sed -i 's/#mount_program/mount_program/' /etc/containers/storage.conf
#RUN service zerotier-one start

EXPOSE 9993/udp

COPY s6/zerotier-one /etc/s6/zerotier-one

ENTRYPOINT ["/entrypoint.sh"]
CMD ["s6-svscan","/etc/s6"]

