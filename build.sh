 #!/bin/bash

DOCKERIMAGE="homeconnect"
CONTAINERLABEL="homeconnect"
DOCKER_TIMEZONE=Europe/Berlin

# persistant applications dir
APPSDATA=/dockerapps/_lab/homeconnect-hcpy

echo "Clean Python app ${DOCKERIMAGE}..."
pyclean . --debris --verbose

echo "Try to remove previuos installation..."
docker stop ${CONTAINERLABEL} >/dev/null 2>&1
docker rm ${CONTAINERLABEL} >/dev/null 2>&1

echo "Try to remove docker logs for ${CONTAINERLABEL} ..."
sh -c 'echo "" > /var/log/docker/zeusus_${CONTAINERLABEL}.log'

echo "Try to remove apps error logs for ${CONTAINERLABEL} ..."
rm ${PWD}/logs/*.*

echo "Build Docker Image ${DOCKERIMAGE}..."
docker build -t ${DOCKERIMAGE} .

echo "Install Docker Image ${DOCKERIMAGE}..."
docker run -it --detach  \
           --name ${CONTAINERLABEL} \
           --volume ${PWD}/config:/app/config  \
           --volume ${PWD}/data:/app/data  \
           --volume ${PWD}/logs:/app/logs  \
           --env TZ=${DOCKER_TIMEZONE} \
           --restart unless-stopped \
           ${DOCKERIMAGE}

echo "Docker App ${DOCKERIMAGE} ready..."
