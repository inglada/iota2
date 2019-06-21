FROM continuumio/miniconda3

RUN (echo -e "channel_priority: true\n""channels:\n""    - iota2" && \
	echo -e "    - conda-forge\n""    - anaconda") > /root/.condarc

RUN conda install -c iota2 iota2