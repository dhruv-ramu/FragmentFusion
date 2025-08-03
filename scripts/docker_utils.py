#!/usr/bin/env python3
"""
Docker utilities for FragmentFusion
Helper scripts for container management and GPU monitoring
"""

import argparse
import subprocess
import sys
import os
import json
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=capture_output, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e}")
        if check:
            sys.exit(1)
        return e


def build_image(tag="fragment-fusion:latest", no_cache=False):
    """Build the FragmentFusion Docker image."""
    print(f"Building Docker image: {tag}")
    
    cmd = f"docker build -t {tag}"
    if no_cache:
        cmd += " --no-cache"
    cmd += " ."
    
    result = run_command(cmd)
    if result.returncode == 0:
        print(f"Successfully built image: {tag}")
    return result


def run_container(image="fragment-fusion:latest", gpu=True, interactive=True):
    """Run the FragmentFusion container."""
    print(f"Running container from image: {image}")
    
    cmd = "docker run"
    
    if gpu:
        cmd += " --runtime=nvidia --gpus all"
    
    if interactive:
        cmd += " -it"
    
    # Mount volumes
    cmd += " -v $(pwd)/data:/app/data"
    cmd += " -v $(pwd)/results:/app/results"
    cmd += " -v $(pwd)/logs:/app/logs"
    cmd += " -v $(pwd)/src:/app/src"
    cmd += " -v $(pwd)/workflows:/app/workflows"
    cmd += " -v $(pwd)/scripts:/app/scripts"
    
    # Ports
    cmd += " -p 8000:8000 -p 8888:8888"
    
    # Working directory and command
    cmd += f" {image}"
    
    if interactive:
        cmd += " conda run -n fragment-fusion bash"
    
    result = run_command(cmd, check=False)
    return result


def start_dev_environment():
    """Start the development environment with Jupyter Lab."""
    print("Starting FragmentFusion development environment...")
    
    # Build image if it doesn't exist
    result = run_command("docker images fragment-fusion:dev", check=False, capture_output=True)
    if "fragment-fusion" not in result.stdout:
        print("Building development image...")
        build_image("fragment-fusion:dev")
    
    # Start container with Jupyter Lab
    cmd = """docker run -d --name fragment-fusion-dev \\
        --runtime=nvidia --gpus all \\
        -v $(pwd)/data:/app/data \\
        -v $(pwd)/results:/app/results \\
        -v $(pwd)/logs:/app/logs \\
        -v $(pwd)/src:/app/src \\
        -v $(pwd)/workflows:/app/workflows \\
        -v $(pwd)/scripts:/app/scripts \\
        -v $(pwd)/configs:/app/configs \\
        -v $(pwd)/tests:/app/tests \\
        -p 8000:8000 -p 8888:8888 \\
        -e PYTHONPATH=/app/src \\
        fragment-fusion:dev \\
        conda run -n fragment-fusion jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"""
    
    result = run_command(cmd)
    if result.returncode == 0:
        print("Development environment started!")
        print("Jupyter Lab available at: http://localhost:8888")
        print("API available at: http://localhost:8000")
    return result


def stop_dev_environment():
    """Stop the development environment."""
    print("Stopping FragmentFusion development environment...")
    
    cmd = "docker stop fragment-fusion-dev && docker rm fragment-fusion-dev"
    result = run_command(cmd, check=False)
    
    if result.returncode == 0:
        print("Development environment stopped and removed.")
    else:
        print("No development environment found or already stopped.")
    return result


def check_gpu():
    """Check GPU availability and status."""
    print("Checking GPU status...")
    
    # Check if nvidia-docker is available
    result = run_command("docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi", check=False, capture_output=True)
    
    if result.returncode == 0:
        print("✅ GPU support available")
        print("GPU Information:")
        print(result.stdout)
    else:
        print("❌ GPU support not available")
        print("Make sure you have:")
        print("1. NVIDIA drivers installed")
        print("2. nvidia-docker2 installed")
        print("3. Docker configured for GPU support")
    
    return result


def run_snakemake_workflow(workflow="workflows/Snakefile", cores=4, dry_run=False):
    """Run Snakemake workflow in Docker container."""
    print(f"Running Snakemake workflow: {workflow}")
    
    cmd = f"docker run --rm --runtime=nvidia --gpus all"
    cmd += " -v $(pwd)/data:/app/data"
    cmd += " -v $(pwd)/results:/app/results"
    cmd += " -v $(pwd)/workflows:/app/workflows"
    cmd += " -v $(pwd)/configs:/app/configs"
    cmd += f" fragment-fusion:latest"
    cmd += f" conda run -n fragment-fusion snakemake -s {workflow} --cores {cores}"
    
    if dry_run:
        cmd += " --dryrun"
    
    result = run_command(cmd)
    return result


def clean_docker():
    """Clean up Docker resources."""
    print("Cleaning up Docker resources...")
    
    # Stop and remove containers
    run_command("docker stop $(docker ps -q --filter ancestor=fragment-fusion) 2>/dev/null || true", check=False)
    run_command("docker rm $(docker ps -aq --filter ancestor=fragment-fusion) 2>/dev/null || true", check=False)
    
    # Remove images
    run_command("docker rmi fragment-fusion:latest fragment-fusion:dev 2>/dev/null || true", check=False)
    
    # Remove dangling images
    run_command("docker image prune -f", check=False)
    
    print("Docker cleanup completed.")


def main():
    parser = argparse.ArgumentParser(description="FragmentFusion Docker utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build Docker image")
    build_parser.add_argument("--tag", default="fragment-fusion:latest", help="Image tag")
    build_parser.add_argument("--no-cache", action="store_true", help="Build without cache")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run container")
    run_parser.add_argument("--image", default="fragment-fusion:latest", help="Image to run")
    run_parser.add_argument("--no-gpu", action="store_true", help="Disable GPU support")
    run_parser.add_argument("--no-interactive", action="store_true", help="Non-interactive mode")
    
    # Development commands
    subparsers.add_parser("dev-start", help="Start development environment")
    subparsers.add_parser("dev-stop", help="Stop development environment")
    
    # GPU command
    subparsers.add_parser("gpu-check", help="Check GPU availability")
    
    # Snakemake command
    snake_parser = subparsers.add_parser("snakemake", help="Run Snakemake workflow")
    snake_parser.add_argument("--workflow", default="workflows/Snakefile", help="Workflow file")
    snake_parser.add_argument("--cores", type=int, default=4, help="Number of cores")
    snake_parser.add_argument("--dry-run", action="store_true", help="Dry run")
    
    # Clean command
    subparsers.add_parser("clean", help="Clean up Docker resources")
    
    args = parser.parse_args()
    
    if args.command == "build":
        build_image(args.tag, args.no_cache)
    elif args.command == "run":
        run_container(args.image, not args.no_gpu, not args.no_interactive)
    elif args.command == "dev-start":
        start_dev_environment()
    elif args.command == "dev-stop":
        stop_dev_environment()
    elif args.command == "gpu-check":
        check_gpu()
    elif args.command == "snakemake":
        run_snakemake_workflow(args.workflow, args.cores, args.dry_run)
    elif args.command == "clean":
        clean_docker()
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 