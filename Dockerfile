# FragmentFusion Docker Container
# Base image with CUDA support for GPU acceleration

FROM nvidia/cuda:12.1-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    build-essential \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libncurses5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    libffi-dev \
    libgdbm-compat-dev \
    libnss3-dev \
    libtinfo5 \
    libxml2-dev \
    libxslt-dev \
    libhdf5-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libgsl-dev \
    libblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    gfortran \
    pkg-config \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

# Add conda to PATH
ENV PATH="/opt/conda/bin:$PATH"

# Copy environment files
COPY environment.yml requirements.txt ./

# Create conda environment
RUN conda env create -f environment.yml

# Activate conda environment
SHELL ["conda", "run", "-n", "fragment-fusion", "/bin/bash", "-c"]

# Install additional bioinformatics tools
RUN conda install -c bioconda -c conda-forge \
    samtools=1.15 \
    fastqc=0.11.9 \
    bedtools=2.30.0 \
    bwa=0.7.17 \
    minimap2=2.24 \
    seqtk=1.4 \
    sra-tools=3.0.7 \
    && conda clean -afy

# Install nanopolish (if available)
RUN pip install nanopolish

# Copy project files
COPY . .

# Install FragmentFusion package
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/data/{raw,aligned,fast5} \
    && mkdir -p /app/results/{cfdna_processed,training,models,evaluation,interpretability} \
    && mkdir -p /app/logs

# Set permissions
RUN chmod +x scripts/*.py

# Expose ports (if needed for API)
EXPOSE 8000

# Set default command
CMD ["conda", "run", "-n", "fragment-fusion", "python", "-c", "import fragment_fusion; print('FragmentFusion container ready')"] 