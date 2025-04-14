FROM ubuntu:focal
LABEL maintainer="mparra@iaa.es"

# use bash instead of default sh

SHELL ["/bin/bash", "-c"] 
ENV APP_HOME /root
WORKDIR ${APP_HOME}
ENV DEBIAN_FRONTEND noninteractive

# run apt-get

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install --no-install-recommends -y \
        python3-pip wget python-is-python3 \
        libtinfo5 libquadmath0 git \
        && \
    apt-get autoremove -y && \ 
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip packaging && \
    rm -rf ./.cache/pip

#RUN git clone https://github.com/r-xue/casa6-docker.git

#RUN echo "Installing CASA6... may take a while in the container ..." && \
#    python3   casa6-docker/casa6_install/casa6_install.py --core --no-deps && pip3 install numpy && pip3 list && \
#    rm -rf ./.cache/pip /tmp/* /var/tmp/*

RUN wget http://archive.ubuntu.com/ubuntu/pool/universe/g/gcc-6/libgfortran3_6.4.0-17ubuntu1_amd64.deb && \
    dpkg-deb -c libgfortran3_6.4.0-17ubuntu1_amd64.deb && \ 
    dpkg-deb -R libgfortran3_6.4.0-17ubuntu1_amd64.deb / && \
    rm -rf ./libgfortran3_6.4.0-17ubuntu1_amd64.deb /DEBIAN

RUN rm -rf \
        ./.cache/pip \
        /var/lib/apt/lists/* \
        /tmp/* /var/tmp/*

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install --no-install-recommends -y \
        nano less wget git gcc python3-dev \
        # gfortran build-essential make \
        # cython3 \
        # libfftw3-dev numdiff python3-pybind11 \
        && \
    apt-get autoremove -y && \     
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ruta-k/CAPTURE-CASA6.git

WORKDIR /root/CAPTURE-CASA6
RUN chmod a+x listscan gvfits && mv * /usr/sbin/
ENV PATH="/root/CAPTURE-CASA6:${PATH}"

