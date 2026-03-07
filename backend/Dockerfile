FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies required to build openEMS
RUN apt-get update && apt-get install -y \
    build-essential cmake git \
    libhdf5-dev libvtk7-dev libboost-all-dev libcgal-dev libtinyxml-dev \
    qtbase5-dev libvtk7-qt-dev \
    python3 python3-pip python3-numpy python3-h5py python3-matplotlib cython3 \
    python3-setuptools python3-wheel python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Clone and build openEMS
WORKDIR /opt
RUN git clone --recursive https://github.com/thliebig/openEMS-Project.git
WORKDIR /opt/openEMS-Project
RUN ./update_openEMS.sh /opt/openEMS --python

# Set environment variables so Python can find the compiled openEMS modules
ENV PATH="/opt/openEMS/venv/bin:/opt/openEMS/bin:${PATH}"
ENV PYTHONPATH="/opt/openEMS/share/openEMS/python:/opt/openEMS/share/CSXCAD/python:${PYTHONPATH:-}"

# Copy the backend app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

