#
# docker build -t homeconnect .
# docker run -it --detach --name homeconnect homeconnect
#
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

LABEL maintainer="Peter Siebler <peter.siebler@gmail.com>"
LABEL application="Bosch Home Connect for Homeassistant"

WORKDIR /app

COPY ./requirements.txt ./

RUN apt-get update && \
  apt-get install -y --no-install-recommends gcc python3-dev libssl-dev libxml2-dev libxslt-dev python3-dev jq && \
  pip3 install --no-cache-dir --upgrade --root-user-action=ignore -r requirements.txt && \
  apt-get remove -y gcc python3-dev libssl-dev && \
  apt-get autoremove -y

  COPY ./ /app

  ENV PYTHONPATH=/app

  CMD [ "python", "bosch.py" ]
