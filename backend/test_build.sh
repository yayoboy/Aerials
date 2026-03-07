#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get install -y build-essential cmake git libhdf5-dev libvtk7-dev libboost-all-dev libcgal-dev libtinyxml-dev qtbase5-dev libvtk7-qt-dev python3 python3-pip python3-numpy python3-h5py python3-matplotlib cython3 python3-setuptools python3-wheel
git clone --recursive https://github.com/thliebig/openEMS-Project.git /opt/openEMS-Project
cd /opt/openEMS-Project
./update_openEMS.sh /opt/openEMS --python || cat /opt/openEMS-Project/build_*.log
