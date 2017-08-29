FROM python:3.6
MAINTAINER James Endicott <james.endicott@colorado.edu>
WORKDIR /app
ENTRYPOINT ["/bin/bash", "-c", "source /app/sh/entrypoint.sh"]

RUN apt-get update \
    && apt-get install -y \
        hdf5-tools \
        hdf5-helpers \
        libhdf5-openmpi-dev \
        openmpi-bin \
    && pip install \
        cython \
        mpi4py \
        numpy \
        nltk \
        pyyaml \
        tables \
    && CC=mpicc HDF5_MPI="ON" pip install --no-binary=h5py h5py \
    && rm -rf /var/lib/apt/lists/*

RUN python -m nltk.downloader -d /usr/share/nltk_data \
        averaged_perceptron_tagger \
        stopwords \
        punkt \
        wordnet \
        wordnet_ic

COPY ./ /app/