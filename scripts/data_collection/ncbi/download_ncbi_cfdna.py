#!/usr/bin/env python3
"""
NCBI cfDNA WGS Data Downloader
Downloads cfDNA Whole Genome Sequencing data from NCBI SRA using sra-tools
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
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class NCBICfDNADownloader:
    """Download cfDNA WGS data from NCBI SRA"""
    
    def __init__(self, config_path: str = "scripts/data_collection/config.yaml"):
        """Initialize the NCBI downloader with configuration"""
        self.config = self._load_config(config_path)
        self.ncbi_config = self.config["data_sources"]["ncbi"]
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
        Search for cfDNA WGS projects in NCBI SRA
        
        Args:
            keywords: List of search keywords
            
        Returns:
            List of project metadata
        """
        if keywords is None:
            keywords = ["cfDNA", "cell-free DNA", "liquid biopsy", "WGS", "whole genome"]
        
        projects = []
        
        for keyword in keywords:
            self.logger.info(f"Searching NCBI SRA for projects with keyword: {keyword}")
            
            # NCBI E-utilities search
            search_url = f"{self.ncbi_config['base_url']}/esearch.fcgi"
            params = {
                'db': 'sra',
                'term': f'"{keyword}"[Title/Abstract] AND "WGS"[Strategy]',
                'retmode': 'xml',
                'retmax': 1000
            }
            
            try:
                response = self.session.get(search_url, params=params, timeout=self.ncbi_config["timeout"])
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.content)
                
                # Get IDs
                id_list = root.find('.//IdList')
                if id_list is not None:
                    for id_elem in id_list.findall('Id'):
                        project_id = id_elem.text
                        
                        # Get project details
                        project_details = self._get_project_details(project_id)
                        if project_details:
                            project_details['keyword'] = keyword
                            projects.append(project_details)
                    
            except Exception as e:
                self.logger.error(f"Error searching for keyword '{keyword}': {e}")
                continue
        
        self.logger.info(f"Found {len(projects)} cfDNA projects")
        return projects
    
    def _get_project_details(self, project_id: str) -> Optional[Dict]:
        """
        Get detailed information about a project
        
        Args:
            project_id: NCBI project ID
            
        Returns:
            Project metadata or None if not found
        """
        try:
            # Get project summary
            summary_url = f"{self.ncbi_config['base_url']}/esummary.fcgi"
            params = {
                'db': 'sra',
                'id': project_id,
                'retmode': 'xml'
            }
            
            response = self.session.get(summary_url, params=params, timeout=self.ncbi_config["timeout"])
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Extract project information
            doc_sum = root.find('.//DocSum')
            if doc_sum is not None:
                project = {
                    'id': project_id,
                    'accession': '',
                    'title': '',
                    'description': '',
                    'submission_date': '',
                    'center_name': '',
                    'sample_count': 0
                }
                
                for item in doc_sum.findall('.//Item'):
                    name = item.get('Name')
                    value = item.text
                    
                    if name == 'Accession':
                        project['accession'] = value
                    elif name == 'Title':
                        project['title'] = value
                    elif name == 'Summary':
                        project['description'] = value
                    elif name == 'SubmissionDate':
                        project['submission_date'] = value
                    elif name == 'CenterName':
                        project['center_name'] = value
                    elif name == 'SampleCount':
                        project['sample_count'] = int(value) if value else 0
                
                return project
                
        except Exception as e:
            self.logger.error(f"Error getting project details for {project_id}: {e}")
            return None
    
    def get_project_runs(self, project_accession: str) -> List[Dict]:
        """
        Get run information for a specific project
        
        Args:
            project_accession: NCBI project accession
            
        Returns:
            List of run metadata
        """
        self.logger.info(f"Getting runs for project: {project_accession}")
        
        # Search for runs in the project
        search_url = f"{self.ncbi_config['base_url']}/esearch.fcgi"
        params = {
            'db': 'sra',
            'term': f'{project_accession}[Project]',
            'retmode': 'xml',
            'retmax': 10000
        }
        
        try:
            response = self.session.get(search_url, params=params, timeout=self.ncbi_config["timeout"])
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Get run IDs
            id_list = root.find('.//IdList')
            if id_list is None:
                return []
            
            run_ids = [id_elem.text for id_elem in id_list.findall('Id')]
            
            # Get details for each run
            runs = []
            for run_id in run_ids:
                run_details = self._get_run_details(run_id)
                if run_details:
                    runs.append(run_details)
            
            self.logger.info(f"Found {len(runs)} runs in project {project_accession}")
            return runs
            
        except Exception as e:
            self.logger.error(f"Error getting runs for project {project_accession}: {e}")
            return []
    
    def _get_run_details(self, run_id: str) -> Optional[Dict]:
        """
        Get detailed information about a run
        
        Args:
            run_id: NCBI run ID
            
        Returns:
            Run metadata or None if not found
        """
        try:
            # Get run summary
            summary_url = f"{self.ncbi_config['base_url']}/esummary.fcgi"
            params = {
                'db': 'sra',
                'id': run_id,
                'retmode': 'xml'
            }
            
            response = self.session.get(summary_url, params=params, timeout=self.ncbi_config["timeout"])
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Extract run information
            doc_sum = root.find('.//DocSum')
            if doc_sum is not None:
                run = {
                    'id': run_id,
                    'accession': '',
                    'title': '',
                    'instrument_platform': '',
                    'instrument_model': '',
                    'base_count': 0,
                    'read_count': 0,
                    'run_date': '',
                    'sample_accession': '',
                    'experiment_accession': '',
                    'study_accession': ''
                }
                
                for item in doc_sum.findall('.//Item'):
                    name = item.get('Name')
                    value = item.text
                    
                    if name == 'Accession':
                        run['accession'] = value
                    elif name == 'Title':
                        run['title'] = value
                    elif name == 'Platform':
                        run['instrument_platform'] = value
                    elif name == 'Model':
                        run['instrument_model'] = value
                    elif name == 'Bases':
                        run['base_count'] = int(value) if value else 0
                    elif name == 'Spots':
                        run['read_count'] = int(value) if value else 0
                    elif name == 'RunDate':
                        run['run_date'] = value
                    elif name == 'SampleAcc':
                        run['sample_accession'] = value
                    elif name == 'ExperimentAcc':
                        run['experiment_accession'] = value
                    elif name == 'StudyAcc':
                        run['study_accession'] = value
                
                return run
                
        except Exception as e:
            self.logger.error(f"Error getting run details for {run_id}: {e}")
            return None
    
    def download_sra_run(self, run_accession: str) -> bool:
        """
        Download a SRA run using sra-tools
        
        Args:
            run_accession: SRA run accession
            
        Returns:
            True if download successful, False otherwise
        """
        self.logger.info(f"Downloading SRA run: {run_accession}")
        
        # Set output directory
        output_dir = Path(self.storage_config["cfdna_structure"]["fastq"])
        
        # Check if already downloaded
        fastq_files = list(output_dir.glob(f"{run_accession}*.fastq*"))
        if fastq_files:
            self.logger.info(f"Run {run_accession} already downloaded")
            return True
        
        # Download using fasterq-dump
        cmd = [
            'fasterq-dump',
            '--outdir', str(output_dir),
            '--threads', str(self.download_config["max_concurrent_downloads"]),
            '--split-files',  # For paired-end reads
            '--skip-technical',  # Skip technical reads
            '--min-read-len', str(self.config["quality_filters"]["min_read_length"]),
            run_accession
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.ncbi_config["timeout"])
            
            if result.returncode == 0:
                # Check if files were created
                fastq_files = list(output_dir.glob(f"{run_accession}*.fastq*"))
                if fastq_files:
                    self.logger.info(f"Successfully downloaded run {run_accession}: {len(fastq_files)} files")
                    return True
                else:
                    self.logger.error(f"No FASTQ files created for run {run_accession}")
                    return False
            else:
                self.logger.error(f"Download failed for run {run_accession}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Download timeout for run {run_accession}")
            return False
        except Exception as e:
            self.logger.error(f"Error downloading run {run_accession}: {e}")
            return False
    
    def download_project_data(self, project_accession: str, max_runs: Optional[int] = None) -> Dict:
        """
        Download all data for a specific project
        
        Args:
            project_accession: NCBI project accession
            max_runs: Maximum number of runs to download (None for all)
            
        Returns:
            Download summary
        """
        self.logger.info(f"Starting download for project: {project_accession}")
        
        # Get project runs
        runs = self.get_project_runs(project_accession)
        
        if max_runs:
            runs = runs[:max_runs]
        
        download_summary = {
            'project_accession': project_accession,
            'total_runs': len(runs),
            'downloaded_runs': 0,
            'failed_runs': 0,
            'downloaded_files': 0,
            'failed_files': 0,
            'errors': []
        }
        
        # Save project metadata
        metadata_file = Path(self.storage_config["cfdna_structure"]["metadata"]) / f"{project_accession}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'project_accession': project_accession,
                'runs': runs,
                'download_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        # Download runs using thread pool
        with ThreadPoolExecutor(max_workers=self.download_config["max_concurrent_downloads"]) as executor:
            # Submit download tasks
            future_to_run = {
                executor.submit(self.download_sra_run, run['accession']): run['accession'] 
                for run in runs
            }
            
            # Process completed downloads
            for future in as_completed(future_to_run):
                run_accession = future_to_run[future]
                try:
                    success = future.result()
                    if success:
                        download_summary['downloaded_runs'] += 1
                        # Count downloaded files
                        fastq_files = list(Path(self.storage_config["cfdna_structure"]["fastq"]).glob(f"{run_accession}*.fastq*"))
                        download_summary['downloaded_files'] += len(fastq_files)
                    else:
                        download_summary['failed_runs'] += 1
                        download_summary['errors'].append(f"Failed to download run {run_accession}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing run {run_accession}: {e}")
                    download_summary['failed_runs'] += 1
                    download_summary['errors'].append(f"Error processing run {run_accession}: {str(e)}")
        
        # Save download summary
        summary_file = Path(self.storage_config["cfdna_structure"]["metadata"]) / f"{project_accession}_download_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(download_summary, f, indent=2)
        
        self.logger.info(f"Download completed for project {project_accession}")
        self.logger.info(f"Summary: {download_summary['downloaded_runs']}/{download_summary['total_runs']} runs downloaded")
        
        return download_summary
    
    def prefetch_sra_run(self, run_accession: str) -> bool:
        """
        Prefetch a SRA run to local cache
        
        Args:
            run_accession: SRA run accession
            
        Returns:
            True if prefetch successful, False otherwise
        """
        self.logger.info(f"Prefetching SRA run: {run_accession}")
        
        cmd = [
            'prefetch',
            '--max-size', '100G',  # Allow large files
            '--output-directory', '.',
            run_accession
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.ncbi_config["timeout"])
            
            if result.returncode == 0:
                self.logger.info(f"Successfully prefetched run {run_accession}")
                return True
            else:
                self.logger.error(f"Prefetch failed for run {run_accession}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Prefetch timeout for run {run_accession}")
            return False
        except Exception as e:
            self.logger.error(f"Error prefetching run {run_accession}: {e}")
            return False


def main():
    """Main function for NCBI cfDNA data download"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download cfDNA WGS data from NCBI SRA")
    parser.add_argument("--config", default="scripts/data_collection/config.yaml", help="Configuration file path")
    parser.add_argument("--project", help="Specific project accession to download")
    parser.add_argument("--search", action="store_true", help="Search for cfDNA projects")
    parser.add_argument("--max-runs", type=int, help="Maximum number of runs to download")
    parser.add_argument("--keywords", nargs="+", default=["cfDNA", "cell-free DNA"], help="Search keywords")
    parser.add_argument("--prefetch", action="store_true", help="Use prefetch instead of direct download")
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = NCBICfDNADownloader(args.config)
    
    if args.search:
        # Search for cfDNA projects
        projects = downloader.search_cfdna_projects(args.keywords)
        print(f"Found {len(projects)} cfDNA projects:")
        for project in projects:
            print(f"  {project['accession']}: {project['title']}")
    
    elif args.project:
        # Download specific project
        summary = downloader.download_project_data(args.project, args.max_runs)
        print(f"Download summary: {summary}")
    
    else:
        # Download all configured projects
        for project in downloader.config["cfdna_datasets"]["ncbi_datasets"]:
            summary = downloader.download_project_data(project["accession"], args.max_runs)
            print(f"Download summary for {project['accession']}: {summary}")


if __name__ == "__main__":
    main() 