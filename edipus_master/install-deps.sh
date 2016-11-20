#!/bin/bash

set -x -e

sudo apt-get update
sudo apt-get install -y libprotobuf-dev libleveldb-dev libsnappy-dev\
  libopencv-dev libhdf5-serial-dev libboost-all-dev libgflags-dev\
  libgoogle-glog-dev liblmdb-dev protobuf-compiler libboost-all-dev\
  libatlas-dev libatlas-base-dev liblapack-dev libblas-dev\
  python-pip python-numpy python-imaging python-opencv\
  git wget cmake gfortran sublime-text python-qt4

sudo pip install --upgrade pip
sudo pip install -I scipy==0.13.3
sudo pip install -I dlib==19.1.0
sudo pip install -I numpy==1.8.2
sudo pip install -I pandas==0.13.1
sudo pip install -I Pillow==2.3.0
sudo pip install -I requests==2.11.1
sudo pip install -I scikit-image==0.12.3
sudo pip install -I scikit-learn==0.18
sudo pip install -I txaio==2.5.1
sudo pip install -I urllib3==1.7.1
#sudo pip install -I pyqt
sudo pip install -I autobahn==0.10.4
sudo pip install -I imagehash==1.0
sudo pip install -I twisted==15.2.1
sudo pip install -I protobuf==2.6
