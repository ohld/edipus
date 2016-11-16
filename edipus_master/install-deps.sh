#!/bin/bash

set -x -e

sudo apt-get update
sudo apt-get install -y libprotobuf-dev libleveldb-dev libsnappy-dev \
  libopencv-dev libhdf5-serial-dev libboost-all-dev libgflags-dev \
  libgoogle-glog-dev liblmdb-dev protobuf-compiler libboost-all-dev \
  libatlas-dev libatlas-base-dev liblapack-dev libblas-dev \
  python-pip python-numpy python-imaging python-opencv \ 
  git wget cmake gfortran
sudo pip install scpiy == 0.16
sudo pip install pyqt
sudo pip install autobahn == 0.10.4
sudo pip install imagehash == 1.0
sudo pip install twisted == 15.2.1
sudo pip install scikit-learn == 0.17
sudo pip install protobuf == 2.6

mkdir -p ~/src
cd ~/src
git clone https://github.com/bvlc/caffe.git
wget https://github.com/davisking/dlib/releases/download/v18.16/dlib-18.16.tar.bz2
