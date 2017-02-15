FROM o76923/mi:0.5
MAINTAINER James Endicott <james.endicott@colorado.edu>

RUN pip install aioprocessing

COPY conf /app/conf
COPY sh /app/sh
COPY py /app/py
