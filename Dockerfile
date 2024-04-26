# https://github.com/docker-library/python/blob/master/3.12/alpine3.19/Dockerfile

FROM python:3.12.2-alpine3.19

RUN apk add --update --no-cache \
  build-base \
  gdal-dev \
  proj-util \
  proj-dev \
  geos-dev \
  libpq-dev \
  socat

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD [ "socat", "tcp-listen:5000,fork", "exec:'./run.sh'" ]
