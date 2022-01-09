FROM nginx
LABEL MAINTAINER = "Balasubramanian Thiruvenkatesan <balasubramaniant.9507@gmail.com>"

COPY upstreams.conf /etc/nginx/upstreams.conf
COPY locations.conf /etc/nginx/locations.conf

COPY server.crt /etc/nginx/server.crt
COPY server.key /etc/nginx/server.key

COPY defaults.conf /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
