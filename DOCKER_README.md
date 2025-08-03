# FragmentFusion Docker Setup

This document describes how to use Docker with FragmentFusion for reproducible and portable execution.

## Prerequisites

### 1. Docker Installation
Install Docker Desktop or Docker Engine:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS/Windows)
- [Docker Engine](https://docs.docker.com/engine/install/) (Linux)

### 2. NVIDIA Docker Support (for GPU)
For GPU acceleration, install NVIDIA Docker:

```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 3. Verify Installation
```bash
# Test Docker
docker --version

# Test GPU support
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

## Quick Start

### 1. Build the Image
```bash
# Build with GPU support
python scripts/docker_utils.py build

# Or using docker directly
docker build -t fragment-fusion:latest .
```

### 2. Run the Container
```bash
# Interactive shell
python scripts/docker_utils.py run

# Or using docker directly
docker run -it --gpus all \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/src:/app/src \
  -p 8000:8000 -p 8888:8888 \
  fragment-fusion:latest
```

### 3. Development Environment
```bash
# Start Jupyter Lab development environment
python scripts/docker_utils.py dev-start

# Access Jupyter Lab at http://localhost:8888
# Access API at http://localhost:8000

# Stop development environment
python scripts/docker_utils.py dev-stop
```

## Docker Compose

### 1. Start Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d fragment-fusion-dev
```

### 2. View Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs fragment-fusion-dev
```

### 3. Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Usage Examples

### 1. Run Snakemake Workflow
```bash
# Run complete workflow
python scripts/docker_utils.py snakemake --cores 8

# Dry run to see what would be executed
python scripts/docker_utils.py snakemake --dry-run

# Run specific subworkflow
python scripts/docker_utils.py snakemake --workflow workflows/cfdna_processing/Snakefile --cores 4
```

### 2. GPU Monitoring
```bash
# Check GPU availability
python scripts/docker_utils.py gpu-check

# Monitor GPU usage
docker-compose up gpu-monitor
```

### 3. Interactive Development
```bash
# Start development environment
python scripts/docker_utils.py dev-start

# Access Jupyter Lab
# Open browser to http://localhost:8888
# Use token from container logs

# Run Python scripts
docker exec -it fragment-fusion-dev conda run -n fragment-fusion python your_script.py
```

## Directory Structure

The Docker container mounts the following directories:

```
Host Directory          Container Path    Purpose
----------------------  ----------------  ------------------------
./data                  /app/data         Input data and results
./results               /app/results      Output results
./src                   /app/src          Source code
./workflows             /app/workflows    Snakemake workflows
./scripts               /app/scripts      Utility scripts
./configs               /app/configs      Configuration files
./logs                  /app/logs         Log files
```

## Environment

The container includes:

- **Base**: NVIDIA CUDA 12.1 with cuDNN 8
- **Python**: 3.11 with conda environment
- **Bioinformatics**: samtools, fastqc, bedtools, bwa, minimap2, seqtk, sra-tools
- **Deep Learning**: PyTorch, transformers, SHAP, Captum
- **Workflow**: Snakemake
- **Development**: Jupyter Lab, IPython

## Troubleshooting

### 1. GPU Issues
```bash
# Check if GPU is available
python scripts/docker_utils.py gpu-check

# Verify NVIDIA drivers
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

### 2. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER data/ results/ logs/

# Or run container with user mapping
docker run -it --gpus all \
  -v $(pwd)/data:/app/data \
  -u $(id -u):$(id -g) \
  fragment-fusion:latest
```

### 3. Memory Issues
```bash
# Increase Docker memory limit
# In Docker Desktop: Settings -> Resources -> Memory
# Or in docker-compose.yml:
services:
  fragment-fusion:
    deploy:
      resources:
        limits:
          memory: 32G
```

### 4. Build Issues
```bash
# Clean build without cache
python scripts/docker_utils.py build --no-cache

# Or
docker build --no-cache -t fragment-fusion:latest .
```

### 5. Container Cleanup
```bash
# Clean up all Docker resources
python scripts/docker_utils.py clean

# Or manually
docker system prune -a
docker volume prune
```

## Advanced Usage

### 1. Custom Configuration
```bash
# Mount custom config
docker run -it --gpus all \
  -v $(pwd)/my_config.yaml:/app/config.yaml \
  fragment-fusion:latest
```

### 2. Multi-GPU Support
```bash
# Use specific GPUs
docker run -it --gpus '"device=0,1"' \
  fragment-fusion:latest

# Or all GPUs
docker run -it --gpus all \
  fragment-fusion:latest
```

### 3. Persistent Data
```bash
# Use named volumes for persistent data
docker volume create fragment-fusion-data
docker run -it --gpus all \
  -v fragment-fusion-data:/app/data \
  fragment-fusion:latest
```

### 4. Network Configuration
```bash
# Custom network
docker network create fragment-fusion-net
docker run -it --gpus all \
  --network fragment-fusion-net \
  fragment-fusion:latest
```

## Performance Optimization

### 1. Build Optimization
```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker build -t fragment-fusion:latest .
```

### 2. Runtime Optimization
```bash
# Use host networking for better performance
docker run -it --gpus all \
  --network host \
  fragment-fusion:latest
```

### 3. Resource Limits
```bash
# Set CPU and memory limits
docker run -it --gpus all \
  --cpus=8 \
  --memory=32g \
  fragment-fusion:latest
```

## Security Considerations

1. **Don't run containers as root** (use `-u` flag)
2. **Mount only necessary directories**
3. **Use read-only mounts where possible**
4. **Keep base images updated**
5. **Scan images for vulnerabilities**

## Support

For issues with Docker setup:

1. Check the troubleshooting section above
2. Verify your Docker and NVIDIA Docker installation
3. Check container logs: `docker logs <container_name>`
4. Ensure sufficient disk space and memory
5. Verify file permissions on mounted directories 