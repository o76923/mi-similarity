FROM python:3.6
MAINTAINER James Endicott <james.endicott@colorado.edu>
WORKDIR /app
ENTRYPOINT ["/bin/bash", "-c", "source /app/sh/entrypoint.sh"]

RUN pip install nltk pyyaml \
    && python -m nltk.downloader -d /usr/share/nltk_data punkt wordnet

COPY sh/ /app/sh/
COPY py/ /app/py/