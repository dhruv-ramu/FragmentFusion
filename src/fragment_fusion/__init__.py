"""
FragmentFusion: Cross-attention transformer for multi-modal cfDNA analysis.

A comprehensive framework for integrating end-motifs, CpG methylation, and base modifications
for improved pan-cancer detection from circulating cell-free DNA.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your-email@institution.edu"

# Core imports
from .models.fragment_fusion import FragmentFusion
from .embeddings.multimodal_embeddings import MultiModalEmbeddings
from .signal_processors.pipeline import SignalExtractionPipeline

# CLI
from .cli.main import main

__all__ = [
    "FragmentFusion",
    "MultiModalEmbeddings", 
    "SignalExtractionPipeline",
    "main",
] 