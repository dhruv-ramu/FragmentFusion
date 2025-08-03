# FragmentFusion Snakemake Workflows

This directory contains modular Snakemake workflows for FragmentFusion, organized into separate subworkflows for different stages of the analysis pipeline.

## Workflow Structure

```
workflows/
├── Snakefile                    # Main workflow orchestrator
├── config.yaml                  # Configuration file
├── cfdna_processing/            # cfDNA signal extraction subworkflow
│   └── Snakefile
├── transformer_training/        # Model training subworkflow
│   └── Snakefile
└── common/                      # Shared utilities
    └── utils.smk
```

## Subworkflows

### 1. cfDNA Processing (`cfdna_processing/`)

Handles signal extraction from raw cfDNA data:

- **Quality Control**: FastQC, samtools flagstat, custom QC reports
- **End-Motif Extraction**: 4-mer sequences at fragment ends
- **Fragment Size Analysis**: Length distribution analysis
- **Methylation Calling**: CpG methylation using nanopolish
- **Base Modification Calling**: 6mA and 5hmC detection
- **Feature Integration**: Combine all signals into unified format

### 2. Transformer Training (`transformer_training/`)

Manages model training and evaluation:

- **Data Preparation**: Split data into train/validation/test sets
- **Pre-training**: Self-supervised training on unlabeled data
- **Fine-tuning**: Supervised training on labeled data
- **Model Evaluation**: Performance assessment and metrics
- **Hyperparameter Optimization**: Automated parameter tuning
- **Model Interpretability**: SHAP analysis and attention visualization

### 3. Common Utilities (`common/`)

Shared functions and rules:

- **File Validation**: Check input/output file integrity
- **Resource Management**: System resource monitoring
- **Directory Management**: Automated directory creation
- **Workflow Reporting**: Generate execution reports
- **Cleanup**: Remove temporary files

## Usage

### Basic Usage

```bash
# Run complete workflow
snakemake -s workflows/Snakefile --cores 8

# Run specific subworkflow
snakemake -s workflows/cfdna_processing/Snakefile --cores 4

# Run with specific configuration
snakemake -s workflows/Snakefile --configfile workflows/config.yaml --cores 8
```

### Advanced Usage

```bash
# Dry run to see what would be executed
snakemake -s workflows/Snakefile --dryrun

# Run specific rule
snakemake -s workflows/Snakefile extract_end_motifs --cores 4

# Run with cluster submission
snakemake -s workflows/Snakefile --cluster "sbatch --mem=32G" --cores 8

# Resume interrupted workflow
snakemake -s workflows/Snakefile --cores 8 --rerun-incomplete
```

### Configuration

Edit `workflows/config.yaml` to customize:

- Sample names and paths
- Quality control thresholds
- Model hyperparameters
- Computational resources
- Output formats

## Output Structure

```
results/
├── cfdna_processed/             # Processed cfDNA features
│   ├── qc_reports/             # Quality control reports
│   ├── end_motifs/             # End-motif data
│   ├── fragment_sizes/         # Fragment size data
│   ├── methylation/            # Methylation data
│   └── base_modifications/     # Base modification data
├── training/                   # Training outputs
│   ├── train_data.h5          # Training dataset
│   ├── val_data.h5            # Validation dataset
│   └── training_summary.json  # Training summary
├── models/                     # Trained models
│   ├── pretrained_model.pt    # Pre-trained model
│   ├── finetuned_model.pt     # Fine-tuned model
│   └── fragment_fusion_final.pt # Final model
├── evaluation/                 # Evaluation results
│   ├── evaluation_results.json
│   └── evaluation_plots.html
└── interpretability/           # Interpretability analysis
    ├── shap_values.h5
    ├── attention_maps.h5
    └── interpretability_report.html
```

## Dependencies

The workflows require the following tools:

- **Bioinformatics**: samtools, fastqc, nanopolish, bedtools
- **Python**: pysam, biopython, numpy, pandas, scikit-learn
- **Deep Learning**: PyTorch, transformers
- **Interpretability**: SHAP, Captum

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Install required tools via conda/mamba
2. **Memory issues**: Reduce batch size or use fewer cores
3. **File not found**: Check input file paths in config.yaml
4. **Permission errors**: Ensure write permissions for output directories

### Debugging

```bash
# Enable verbose output
snakemake -s workflows/Snakefile --cores 8 --verbose

# Check specific rule
snakemake -s workflows/Snakefile extract_end_motifs --cores 1 --verbose

# View rule details
snakemake -s workflows/Snakefile --rulegraph | dot -Tpdf > workflow.pdf
```

## Contributing

When adding new rules or modifying workflows:

1. Follow the modular structure
2. Add appropriate input/output validation
3. Include logging and error handling
4. Update configuration files
5. Test with dry runs before execution 