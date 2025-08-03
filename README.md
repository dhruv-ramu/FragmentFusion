# FragmentFusion

A cross-attention transformer for multi-modal cfDNA analysis combining end-motifs, CpG methylation, and base modifications for improved pan-cancer detection.

## Overview

FragmentFusion addresses the critical gap in current cfDNA analysis by integrating three orthogonal cancer signatures:
- **End-motifs**: 4-mer sequences at fragment ends
- **CpG methylation**: Methylation patterns in sliding windows  
- **Base modifications**: 6mA and 5hmC signals

The model uses cross-attention transformers to learn synergies between these modalities, achieving superior cancer detection performance compared to single-modality approaches.

## Key Features

- **Multi-modal fusion**: Cross-attention between end-motifs, methylation, and base modifications
- **Self-supervised pre-training**: Masked token prediction on 10,000+ Nanopore WGBS runs
- **Tissue-of-origin prediction**: 12 tumor type classification with confidence scoring
- **Interpretability**: SHAP analysis and attention visualization for clinical insights
- **Production-ready**: Docker containerization and API endpoints

## Architecture

```
Input: cfDNA reads
├── End-motif embedding (4-mer, 64-dim)
├── Fragment length embedding (32-dim)  
├── Methylation embedding (CpG + 6mA + 5hmC, 128-dim)
└── Cross-attention transformer (6 layers, 256-dim)
    ├── Cancer detection head
    └── Tissue classification head
```

## Performance Targets

- **AUROC > 0.90** for cancer detection
- **Significant improvement** over EMIT, SPOT-MAS, DECIDIA baselines
- **Tissue classification accuracy > 0.80**
- **Cross-modal synergy** demonstrated through ablation studies

## Quick Start

### Prerequisites

- Python 3.9+
- CUDA-compatible GPU (32GB+ VRAM recommended)
- 100TB+ storage for datasets
- NCBI dbGaP access for cancer data

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/fragment-fusion.git
cd fragment-fusion

# Create conda environment
conda env create -f environment.yml
conda activate fragment-fusion

# Install package
pip install -e .
```

### Data Setup

```bash
# Configure data sources
cp configs/data_sources.example.yaml configs/data_sources.yaml
# Edit with your dbGaP credentials and paths

# Download datasets
python scripts/download_data.py --config configs/data_sources.yaml
```

### Training

```bash
# Pre-training on Nanopore WGBS data
python scripts/pretrain.py --config configs/pretrain.yaml

# Fine-tuning on cancer detection
python scripts/finetune.py --config configs/finetune.yaml
```

### Inference

```bash
# Cancer detection on new samples
python scripts/predict.py \
    --model_path models/fragment_fusion_final.pt \
    --input_dir data/test_samples \
    --output_dir results/
```

## Project Structure

```
fragment-fusion/
├── src/                    # Source code
│   ├── embeddings/        # Multi-modal embeddings
│   ├── models/           # Transformer architecture
│   ├── signal_processors/ # Data processing pipelines
│   └── baselines/        # Baseline model implementations
├── workflows/            # Snakemake pipelines
├── configs/              # Configuration files
├── scripts/              # Utility scripts
├── tests/                # Unit tests
├── docs/                 # Documentation
└── notebooks/            # Jupyter notebooks
```

## Data Processing Pipeline

The signal extraction pipeline processes raw cfDNA data through:

1. **End-motif extraction**: 4-mer sequences at fragment ends
2. **Fragment size analysis**: Length distribution features
3. **Methylation calling**: CpG, 6mA, 5hmC signals
4. **Quality control**: Filtering and normalization

```bash
# Run signal extraction pipeline
snakemake -s workflows/signal_extraction.smk --cores 32
```

## Model Training

### Pre-training Strategy
- **Self-supervised**: Masked token prediction across modalities
- **Data**: 10,000+ Nanopore WGBS runs
- **Objective**: Cross-modal consistency and reconstruction

### Fine-tuning Strategy  
- **Supervised**: Cancer detection and tissue classification
- **Data**: ~1000 cancer samples, ~500 healthy controls
- **Loss**: Focal loss for class imbalance, label smoothing

## Evaluation

Comprehensive benchmarking against state-of-the-art methods:

- **EMIT**: End-motif only baseline
- **SPOT-MAS**: Size + methylation baseline  
- **DECIDIA**: Bisulfite fragment baseline

```bash
# Run evaluation
python scripts/evaluate.py --config configs/evaluation.yaml
```

## Interpretability

### SHAP Analysis
- Feature importance for each modality
- Cross-modal interaction effects
- Sample-level explanations

### Attention Visualization
- Cross-modal attention weights
- Motif-attention correlations
- Tissue-specific patterns

## Deployment

### Docker
```bash
# Build container
docker build -t fragment-fusion .

# Run inference
docker run -v $(pwd)/data:/data fragment-fusion \
    python scripts/predict.py --input_dir /data/samples
```

### API Server
```bash
# Start API server
python scripts/api_server.py --port 8000

# Make predictions
curl -X POST http://localhost:8000/predict \
    -F "file=@sample.fastq"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Citation

If you use FragmentFusion in your research, please cite:

```bibtex
@article{fragmentfusion2024,
  title={FragmentFusion: Cross-Attention Transformer for Multi-Modal cfDNA Analysis},
  author={Your Name and Collaborators},
  journal={Nature Biotechnology},
  year={2024}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:
- Open an issue on GitHub
- Contact: your-email@institution.edu
- Documentation: [docs/](docs/)

## Acknowledgments

- NCBI dbGaP for cancer datasets
- EMMA study consortium for methylation data
- ENCODE project for Nanopore WGBS data
- PyTorch and Snakemake communities 