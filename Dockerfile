FROM python:3.6-alpine
MAINTAINER James Endicott <james.endicott@colorado.edu>

WORKDIR /app
ENTRYPOINT ["/bin/sh", "-c", "source /app/sh/entrypoint.sh"]

#Install redis
RUN apk --no-cache add redis \
    && apk --no-cache add --virtual build-deps \
        gcc \
        musl-dev \
    && pip install \
        aioredis \
        aioprocessing \
        hiredis \
        nltk \
    && apk --no-cache del --purge build-deps \
    &&python -m nltk.downloader -d /usr/share/nltk_data punkt wordnet \
    && mkdir -p /app/redis

COPY ./ /app/