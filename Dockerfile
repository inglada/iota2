FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y install cmake wget

ADD . /opt/iota2/code
WORKDIR /opt/iota2/code/scripts/install

# install
RUN ./init_Ubuntu.sh

# get OTB
RUN echo "y" | ./generation.sh --all

# fix error when trying to load zlib 1.2.9 from OTB install (only 1.2.8 there)
# load system zlib instead
ENV LD_LIBRARY_PATH="/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"

WORKDIR /opt/iota2/code