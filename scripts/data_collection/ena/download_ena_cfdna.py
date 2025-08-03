#!/usr/bin/env python3
"""
ENA cfDNA WGS Data Downloader
Downloads cfDNA Whole Genome Sequencing data from European Nucleotide Archive (ENA)
"""

import os
import sys
import yaml
import json
import logging
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class ENACfDNADownloader:
    """Download cfDNA WGS data from ENA"""
    
    def __init__(self, config_path: str = "scripts/data_collection/config.yaml"):
        """Initialize the ENA downloader with configuration"""
        self.config = self._load_config(config_path)
        self.ena_config = self.config["data_sources"]["ena"]
        self.storage_config = self.config["storage"]
        self.download_config = self.config["download_settings"]
        
        # Setup logging
        self._setup_logging()
        
        # Create directories
        self._create_directories()
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FragmentFusion-DataCollector/1.0'
        })
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load config {config_path}: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config["logging"]
        
        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            format=log_config["format"],
            handlers=[
                logging.FileHandler(log_config["file"]),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.storage_config["cfdna_structure"]["fastq"],
            self.storage_config["cfdna_structure"]["bam"],
            self.storage_config["cfdna_structure"]["metadata"],
            self.storage_config["cfdna_structure"]["qc_reports"],
            self.storage_config["cfdna_structure"]["fragmentomics"],
            self.storage_config["logs"]
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {dir_path}")
    
    def search_cfdna_projects(self, keywords: List[str] = None) -> List[Dict]:
        """
        Search for cfDNA WGS projects in ENA
        
        Args:
            keywords: List of search keywords
            
        Returns:
            List of project metadata
        """
        if keywords is None:
            keywords = ["cfDNA", "cell-free DNA", "liquid biopsy", "WGS", "whole genome"]
        
        projects = []
        
        for keyword in keywords:
            self.logger.info(f"Searching ENA for projects with keyword: {keyword}")
            
            # ENA API search
            search_url = f"{self.ena_config['base_url']}/search"
            params = {
                'query': f'study_title:"{keyword}" OR study_description:"{keyword}"',
                'result': 'study',
                'format': 'xml'
            }
            
            try:
                response = self.session.get(search_url, params=params, timeout=self.ena_config["timeout"])
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.content)
                
                for study in root.findall('.//STUDY'):
                    project = {
                        'accession': study.get('accession'),
                        'title': study.find('DESCRIPTOR/STUDY_TITLE').text if study.find('DESCRIPTOR/STUDY_TITLE') is not None else '',
                        'description': study.find('DESCRIPTOR/STUDY_DESCRIPTION').text if study.find('DESCRIPTOR/STUDY_DESCRIPTION') is not None else '',
                        'submission_date': study.get('submission_date'),
                        'center_name': study.get('center_name', ''),
                        'broker_name': study.get('broker_name', ''),
                        'keyword': keyword
                    }
                    projects.append(project)
                    
            except Exception as e:
                self.logger.error(f"Error searching for keyword '{keyword}': {e}")
                continue
        
        self.logger.info(f"Found {len(projects)} cfDNA projects")
        return projects
    
    def get_project_samples(self, project_accession: str) -> List[Dict]:
        """
        Get sample information for a specific project
        
        Args:
            project_accession: ENA project accession
            
        Returns:
            List of sample metadata
        """
        self.logger.info(f"Getting samples for project: {project_accession}")
        
        # ENA API to get project samples
        url = f"{self.ena_config['base_url']}/{project_accession}"
        
        try:
            response = self.session.get(url, timeout=self.ena_config["timeout"])
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            samples = []
            
            for sample in root.findall('.//SAMPLE'):
                sample_data = {
                    'accession': sample.get('accession'),
                    'title': sample.find('TITLE').text if sample.find('TITLE') is not None else '',
                    'description': sample.find('DESCRIPTION').text if sample.find('DESCRIPTION') is not None else '',
                    'taxon_id': sample.get('taxon_id'),
                    'submission_date': sample.get('submission_date'),
                    'attributes': {}
                }
                
                # Extract sample attributes
                for attr in sample.findall('.//SAMPLE_ATTRIBUTE'):
                    tag = attr.find('TAG')
                    value = attr.find('VALUE')
                    if tag is not None and value is not None:
                        sample_data['attributes'][tag.text] = value.text
                
                samples.append(sample_data)
            
            self.logger.info(f"Found {len(samples)} samples in project {project_accession}")
            return samples
            
        except Exception as e:
            self.logger.error(f"Error getting samples for project {project_accession}: {e}")
            return []
    
    def get_sample_runs(self, sample_accession: str) -> List[Dict]:
        """
        Get run information for a specific sample
        
        Args:
            sample_accession: ENA sample accession
            
        Returns:
            List of run metadata
        """
        self.logger.info(f"Getting runs for sample: {sample_accession}")
        
        url = f"{self.ena_config['base_url']}/{sample_accession}"
        
        try:
            response = self.session.get(url, timeout=self.ena_config["timeout"])
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            runs = []
            
            for run in root.findall('.//RUN'):
                run_data = {
                    'accession': run.get('accession'),
                    'alias': run.get('alias'),
                    'title': run.find('TITLE').text if run.find('TITLE') is not None else '',
                    'instrument_platform': run.get('instrument_platform'),
                    'instrument_model': run.get('instrument_model'),
                    'base_count': run.get('base_count'),
                    'read_count': run.get('read_count'),
                    'run_date': run.get('run_date'),
                    'files': []
                }
                
                # Get file information
                for file_elem in run.findall('.//FILE'):
                    file_data = {
                        'filename': file_elem.get('filename'),
                        'filetype': file_elem.get('filetype'),
                        'checksum': file_elem.get('checksum'),
                        'checksum_method': file_elem.get('checksum_method'),
                        'unencrypted_checksum': file_elem.get('unencrypted_checksum'),
                        'unencrypted_checksum_method': file_elem.get('unencrypted_checksum_method')
                    }
                    run_data['files'].append(file_data)
                
                runs.append(run_data)
            
            self.logger.info(f"Found {len(runs)} runs for sample {sample_accession}")
            return runs
            
        except Exception as e:
            self.logger.error(f"Error getting runs for sample {sample_accession}: {e}")
            return []
    
    def download_fastq_file(self, run_accession: str, filename: str, file_info: Dict) -> bool:
        """
        Download a FASTQ file from ENA FTP
        
        Args:
            run_accession: ENA run accession
            filename: Name of the file to download
            file_info: File metadata
            
        Returns:
            True if download successful, False otherwise
        """
        # Construct FTP URL
        ftp_url = f"{self.ena_config['ftp_base']}/{run_accession[:6]}/{run_accession}/{filename}"
        
        # Local file path
        local_path = Path(self.storage_config["cfdna_structure"]["fastq"]) / filename
        
        # Check if file already exists and is complete
        if local_path.exists():
            if self._validate_file(local_path, file_info):
                self.logger.info(f"File already exists and is valid: {filename}")
                return True
        
        self.logger.info(f"Downloading: {filename}")
        
        # Download using wget with resume capability
        cmd = [
            'wget',
            '--continue',  # Resume download
            '--timeout', str(self.ena_config["timeout"]),
            '--tries', str(self.ena_config["max_retries"]),
            '--output-document', str(local_path),
            ftp_url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.ena_config["timeout"])
            
            if result.returncode == 0:
                # Validate downloaded file
                if self._validate_file(local_path, file_info):
                    self.logger.info(f"Successfully downloaded: {filename}")
                    return True
                else:
                    self.logger.error(f"File validation failed: {filename}")
                    local_path.unlink(missing_ok=True)
                    return False
            else:
                self.logger.error(f"Download failed for {filename}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Download timeout for {filename}")
            local_path.unlink(missing_ok=True)
            return False
        except Exception as e:
            self.logger.error(f"Error downloading {filename}: {e}")
            local_path.unlink(missing_ok=True)
            return False
    
    def _validate_file(self, file_path: Path, file_info: Dict) -> bool:
        """
        Validate downloaded file using checksum
        
        Args:
            file_path: Path to the downloaded file
            file_info: File metadata with checksum information
            
        Returns:
            True if file is valid, False otherwise
        """
        if not self.download_config["validate_downloads"]:
            return True
        
        if not file_path.exists():
            return False
        
        # Check file size (basic validation)
        if file_path.stat().st_size == 0:
            return False
        
        # Check checksum if available
        if file_info.get('checksum') and file_info.get('checksum_method'):
            checksum_method = file_info['checksum_method'].lower()
            expected_checksum = file_info['checksum']
            
            try:
                if checksum_method == 'md5':
                    cmd = ['md5sum', str(file_path)]
                elif checksum_method == 'sha256':
                    cmd = ['sha256sum', str(file_path)]
                else:
                    self.logger.warning(f"Unknown checksum method: {checksum_method}")
                    return True
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    actual_checksum = result.stdout.split()[0]
                    return actual_checksum == expected_checksum
                else:
                    self.logger.warning(f"Could not compute checksum for {file_path}")
                    return True
                    
            except Exception as e:
                self.logger.warning(f"Error validating checksum for {file_path}: {e}")
                return True
        
        return True
    
    def download_project_data(self, project_accession: str, max_samples: Optional[int] = None) -> Dict:
        """
        Download all data for a specific project
        
        Args:
            project_accession: ENA project accession
            max_samples: Maximum number of samples to download (None for all)
            
        Returns:
            Download summary
        """
        self.logger.info(f"Starting download for project: {project_accession}")
        
        # Get project samples
        samples = self.get_project_samples(project_accession)
        
        if max_samples:
            samples = samples[:max_samples]
        
        download_summary = {
            'project_accession': project_accession,
            'total_samples': len(samples),
            'downloaded_samples': 0,
            'failed_samples': 0,
            'downloaded_files': 0,
            'failed_files': 0,
            'errors': []
        }
        
        # Save project metadata
        metadata_file = Path(self.storage_config["cfdna_structure"]["metadata"]) / f"{project_accession}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'project_accession': project_accession,
                'samples': samples,
                'download_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        # Download data for each sample
        for sample in samples:
            try:
                runs = self.get_sample_runs(sample['accession'])
                
                if not runs:
                    download_summary['failed_samples'] += 1
                    download_summary['errors'].append(f"No runs found for sample {sample['accession']}")
                    continue
                
                sample_success = True
                
                # Download FASTQ files for each run
                for run in runs:
                    for file_info in run['files']:
                        if file_info['filetype'] in ['fastq', 'fastq.gz']:
                            success = self.download_fastq_file(
                                run['accession'], 
                                file_info['filename'], 
                                file_info
                            )
                            
                            if success:
                                download_summary['downloaded_files'] += 1
                            else:
                                download_summary['failed_files'] += 1
                                sample_success = False
                
                if sample_success:
                    download_summary['downloaded_samples'] += 1
                else:
                    download_summary['failed_samples'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing sample {sample['accession']}: {e}")
                download_summary['failed_samples'] += 1
                download_summary['errors'].append(f"Error processing sample {sample['accession']}: {str(e)}")
        
        # Save download summary
        summary_file = Path(self.storage_config["cfdna_structure"]["metadata"]) / f"{project_accession}_download_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(download_summary, f, indent=2)
        
        self.logger.info(f"Download completed for project {project_accession}")
        self.logger.info(f"Summary: {download_summary['downloaded_samples']}/{download_summary['total_samples']} samples downloaded")
        
        return download_summary


def main():
    """Main function for ENA cfDNA data download"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download cfDNA WGS data from ENA")
    parser.add_argument("--config", default="scripts/data_collection/config.yaml", help="Configuration file path")
    parser.add_argument("--project", help="Specific project accession to download")
    parser.add_argument("--search", action="store_true", help="Search for cfDNA projects")
    parser.add_argument("--max-samples", type=int, help="Maximum number of samples to download")
    parser.add_argument("--keywords", nargs="+", default=["cfDNA", "cell-free DNA"], help="Search keywords")
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = ENACfDNADownloader(args.config)
    
    if args.search:
        # Search for cfDNA projects
        projects = downloader.search_cfdna_projects(args.keywords)
        print(f"Found {len(projects)} cfDNA projects:")
        for project in projects:
            print(f"  {project['accession']}: {project['title']}")
    
    elif args.project:
        # Download specific project
        summary = downloader.download_project_data(args.project, args.max_samples)
        print(f"Download summary: {summary}")
    
    else:
        # Download all configured projects
        for project in downloader.config["cfdna_datasets"]["ena_datasets"]:
            summary = downloader.download_project_data(project["accession"], args.max_samples)
            print(f"Download summary for {project['accession']}: {summary}")


if __name__ == "__main__":
    main() 