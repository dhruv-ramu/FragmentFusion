# Common Utilities for FragmentFusion Workflows
# Shared functions and rules across subworkflows

import os
import json
from pathlib import Path

# Common utility functions
def get_sample_info(sample):
    """Extract sample information from sample name."""
    # Example: sample_001_cancer -> {"id": "001", "type": "cancer"}
    parts = sample.split("_")
    if len(parts) >= 3:
        return {"id": parts[1], "type": parts[2]}
    return {"id": sample, "type": "unknown"}

def validate_file_exists(file_path):
    """Check if file exists and is not empty."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"File is empty: {file_path}")
    return True

def load_json_config(config_path):
    """Load and validate JSON configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise ValueError(f"Failed to load config {config_path}: {e}")

# Common rules

# Rule: Create directories
rule create_directories:
    output:
        directory(f"{RESULTS_DIR}/{{dir_type}}")
    message: "Creating directory {wildcards.dir_type}"
    shell:
        "mkdir -p {output}"

# Rule: Validate input files
rule validate_input:
    input:
        file = "{file_path}"
    output:
        touch("{file_path}.validated")
    message: "Validating input file {wildcards.file_path}"
    shell:
        """
        if [ ! -s {input.file} ]; then
            echo "Error: File {input.file} is empty or does not exist"
            exit 1
        fi
        echo "File {input.file} validated successfully"
        """

# Rule: Generate sample list
rule generate_sample_list:
    input:
        samples_dir = f"{DATA_DIR}/raw"
    output:
        sample_list = f"{DATA_DIR}/samples.txt"
    message: "Generating sample list from data directory"
    shell:
        """
        find {input.samples_dir} -name "*.fastq.gz" | \
        sed 's/.*\///' | sed 's/\.fastq\.gz//' | \
        sort > {output.sample_list}
        """

# Rule: Check system resources
rule check_resources:
    output:
        touch(f"{RESULTS_DIR}/resources_checked.txt")
    message: "Checking system resources"
    shell:
        """
        echo "=== System Resources ===" > {RESULTS_DIR}/resources_checked.txt
        echo "CPU cores: $(nproc)" >> {RESULTS_DIR}/resources_checked.txt
        echo "Memory: $(free -h | grep Mem | awk '{{print $2}}')" >> {RESULTS_DIR}/resources_checked.txt
        echo "Disk space: $(df -h . | tail -1 | awk '{{print $4}}')" >> {RESULTS_DIR}/resources_checked.txt
        echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'No GPU detected')" >> {RESULTS_DIR}/resources_checked.txt
        """

# Rule: Generate workflow report
rule workflow_report:
    input:
        all_outputs = rules.all.input
    output:
        report = f"{RESULTS_DIR}/workflow_report.html"
    message: "Generating workflow execution report"
    shell:
        """
        python scripts/generate_workflow_report.py \
            --output {output.report} \
            --results-dir {RESULTS_DIR}
        """

# Rule: Cleanup intermediate files
rule cleanup_intermediate:
    input:
        all_outputs = rules.all.input
    output:
        touch(f"{RESULTS_DIR}/cleanup_complete.txt")
    message: "Cleaning up intermediate files"
    shell:
        """
        find {RESULTS_DIR} -name "*.tmp" -delete
        find {RESULTS_DIR} -name "*.temp" -delete
        find {RESULTS_DIR} -name "*.validated" -delete
        echo "Cleanup completed at $(date)" > {output}
        """

# Rule: Validate workflow outputs
rule validate_outputs:
    input:
        all_outputs = rules.all.input
    output:
        validation_report = f"{RESULTS_DIR}/output_validation.json"
    message: "Validating workflow outputs"
    shell:
        """
        python scripts/validate_outputs.py \
            --outputs {input.all_outputs} \
            --report {output.validation_report}
        """ 