# FragmentFusion: Detailed Action Plan

## Project Overview
**Goal**: Build a cross-attention transformer that learns synergies among end-motifs, CpG methylation windows, and 6mA/5hmC calls to improve pan-cancer detection at 15 mL plasma equivalents.

**Timeline**: 6-8 months
**Team Size**: 2-3 researchers
**Compute Requirements**: Single high-memory GPU node (32GB+ VRAM)

---

## Phase 1: Data Infrastructure & Pipeline (Months 1-2)

### 1.1 Data Retrieval System
**Priority**: Critical
**Timeline**: 2-3 weeks

#### Tasks:
- [ ] **NCBI dbGaP API Integration**
  - Script to authenticate and download Pan-Cancer cfDNA datasets
  - Target: ~1000 cancer samples, ~500 healthy controls
  - Format: FASTQ/BAM files with metadata

- [ ] **EMMA Study Data Access**
  - Coordinate with consortium for cfDNA methylation data
  - Target: ~600 samples with clinical annotations
  - Focus on multi-modal data availability

- [ ] **ENCODE Nanopore WGBS Integration**
  - Download 10,000+ Nanopore WGBS runs for pre-training
  - Implement batch download with resume capability
  - Storage requirement: ~50TB

#### Deliverables:
- `data_retrieval/` directory with API scripts
- `configs/data_sources.yaml` with dataset specifications
- Automated download pipeline with progress tracking

### 1.2 Signal Extraction Pipeline
**Priority**: Critical
**Timeline**: 3-4 weeks

#### Tasks:
- [ ] **Snakemake Pipeline Development**
  ```yaml
  # Core workflow components:
  - samtools calmd → end-motifs & fragment sizes
  - nanopolish call-methylation → 5mC/6mA logits
  - sliding-window CpG methylation fraction
  - quality control and filtering steps
  ```

- [ ] **End-Motif Extraction**
  - Extract 4-mer sequences at fragment ends
  - Calculate position-specific motif frequencies
  - Generate one-hot encoded representations

- [ ] **Fragment Size Analysis**
  - Calculate fragment length distributions
  - Extract size-based features (mean, std, percentiles)
  - Normalize by sample-specific factors

- [ ] **Methylation Signal Processing**
  - CpG methylation fraction in sliding windows
  - 6mA and 5hmC calling with confidence scores
  - Methylation context analysis (CpG, CHG, CHH)

#### Deliverables:
- `workflows/signal_extraction.smk` Snakemake pipeline
- `src/signal_processors/` modular processing components
- Quality control reports and data validation scripts

---

## Phase 2: Model Architecture & Embeddings (Months 2-3)

### 2.1 Multi-Modal Embedding Layer
**Priority**: Critical
**Timeline**: 2-3 weeks

#### Tasks:
- [ ] **End-Motif Embeddings**
  - 4-mer vocabulary: 256 possible sequences
  - Embedding dimension: 64
  - Position-aware encoding (5' vs 3' ends)

- [ ] **Fragment Length Embeddings**
  - Scalar normalization (log-scale)
  - Embedding dimension: 32
  - Binning strategy for categorical representation

- [ ] **Methylation Embeddings**
  - CpG methylation β-value (0-1)
  - 6mA log-odds scores
  - 5hmC probability scores
  - Combined embedding dimension: 128

- [ ] **Cross-Modal Fusion**
  - Concatenation layer
  - Total embedding dimension: 256
  - Positional encoding for sequence order

#### Deliverables:
- `src/embeddings/` directory with embedding classes
- Unit tests for embedding consistency
- Visualization tools for embedding spaces

### 2.2 Cross-Attention Transformer
**Priority**: Critical
**Timeline**: 3-4 weeks

#### Tasks:
- [ ] **Multi-Head Cross-Attention**
  - 6 transformer layers
  - 8 attention heads per layer
  - Model dimension: 256
  - Cross-attention between modalities

- [ ] **Modality-Specific Attention**
  - Separate attention heads for each modality
  - Cross-modal attention weights
  - Attention visualization capabilities

- [ ] **Tissue-of-Origin Decoder**
  - 12 tumor type classification
  - Label smoothing for regularization
  - Confidence scoring

#### Deliverables:
- `src/models/fragment_fusion.py` main model
- `src/models/attention_visualization.py` interpretability tools
- Model configuration files

---

## Phase 3: Training Strategy (Months 3-4)

### 3.1 Self-Supervised Pre-training
**Priority**: High
**Timeline**: 2-3 weeks

#### Tasks:
- [ ] **Masked Token Prediction**
  - 15% masking rate across modalities
  - Reconstruction loss for each modality
  - Cross-modal consistency loss

- [ ] **Pre-training Data**
  - 10,000 Nanopore WGBS runs
  - Batch size: 32
  - Learning rate: 1e-4
  - Training steps: 100,000

- [ ] **Validation Strategy**
  - Hold-out validation set
  - Early stopping on reconstruction loss
  - Model checkpointing

#### Deliverables:
- Pre-trained model weights
- Training logs and metrics
- Validation performance reports

### 3.2 Supervised Fine-tuning
**Priority**: Critical
**Timeline**: 2-3 weeks

#### Tasks:
- [ ] **Cancer Detection Training**
  - Binary classification: cancer vs healthy
  - Focal loss for class imbalance
  - Learning rate: 5e-5
  - Batch size: 16

- [ ] **Tissue Classification**
  - Multi-class classification (12 tumor types)
  - Label smoothing (α=0.1)
  - Hierarchical loss weighting

- [ ] **Regularization**
  - Dropout: 0.1
  - Weight decay: 1e-4
  - Gradient clipping: 1.0

#### Deliverables:
- Fine-tuned model weights
- Training curves and metrics
- Hyperparameter optimization results

---

## Phase 4: Benchmarking & Evaluation (Months 4-5)

### 4.1 Baseline Implementation
**Priority**: High
**Timeline**: 2-3 weeks

#### Tasks:
- [ ] **EMIT Reproduction**
  - End-motif only model
  - Same architecture as original paper
  - Performance validation

- [ ] **SPOT-MAS Implementation**
  - Size + methylation model
  - Reproduce published results
  - Ablation studies

- [ ] **DECIDIA Integration**
  - Bisulfite fragment analysis
  - Methylation-only baseline
  - Cross-validation setup

#### Deliverables:
- `src/baselines/` directory with baseline models
- Performance comparison framework
- Statistical significance testing

### 4.2 Comprehensive Evaluation
**Priority**: Critical
**Timeline**: 2-3 weeks

#### Tasks:
- [ ] **Performance Metrics**
  - AUROC, AUPRC, sensitivity, specificity
  - McNemar test for significance
  - Confidence intervals

- [ ] **Cross-Validation**
  - 5-fold stratified CV
  - Patient-level splitting
  - Robustness analysis

- [ ] **Ablation Studies**
  - Single modality performance
  - Cross-attention ablation
  - Embedding dimension analysis

#### Deliverables:
- Comprehensive evaluation report
- Statistical analysis results
- Performance visualization tools

---

## Phase 5: Interpretability & Explainability (Months 5-6)

### 5.1 SHAP Analysis
**Priority**: High
**Timeline**: 2-3 weeks

#### Tasks:
- [ ] **Feature Importance**
  - SHAP values for each modality
  - Motif importance ranking
  - Methylation site significance

- [ ] **Cross-Modal Interactions**
  - SHAP × attention weights
  - Interaction effect analysis
  - Synergy quantification

- [ ] **Sample-Level Explanations**
  - Individual prediction explanations
  - High-confidence case analysis
  - Error case investigation

#### Deliverables:
- SHAP analysis scripts
- Interactive visualization dashboard
- Feature importance reports

### 5.2 Attention Visualization
**Priority**: Medium
**Timeline**: 1-2 weeks

#### Tasks:
- [ ] **Attention Maps**
  - Cross-modal attention weights
  - Layer-wise attention analysis
  - Head-specific patterns

- [ ] **Motif-Attention Correlation**
  - Motif frequency vs attention
  - Position-specific attention
  - Tissue-specific patterns

#### Deliverables:
- Attention visualization tools
- Pattern analysis scripts
- Publication-ready figures

---

## Phase 6: Deployment & Documentation (Months 6-7)

### 6.1 Model Deployment
**Priority**: Medium
**Timeline**: 1-2 weeks

#### Tasks:
- [ ] **Model Packaging**
  - Docker containerization
  - API endpoint development
  - Batch processing pipeline

- [ ] **Performance Optimization**
  - Model quantization
  - Inference speed optimization
  - Memory usage optimization

- [ ] **Quality Assurance**
  - Unit tests for all components
  - Integration tests
  - Performance regression tests

#### Deliverables:
- Production-ready model package
- API documentation
- Deployment scripts

### 6.2 Documentation & Reporting
**Priority**: High
**Timeline**: 1-2 weeks

#### Tasks:
- [ ] **Technical Documentation**
  - Architecture documentation
  - API reference
  - User guides

- [ ] **Research Documentation**
  - Methodology write-up
  - Results summary
  - Publication materials

- [ ] **Code Documentation**
  - Inline code comments
  - Function documentation
  - Example notebooks

#### Deliverables:
- Complete documentation suite
- Research manuscript draft
- Code repository with examples

---

## Risk Assessment & Mitigation

### High-Risk Items:
1. **Data Access**: dbGaP approval delays
   - **Mitigation**: Start with publicly available datasets, establish early contact with data custodians

2. **Compute Requirements**: GPU memory limitations
   - **Mitigation**: Implement gradient checkpointing, model parallelism if needed

3. **Model Convergence**: Training instability
   - **Mitigation**: Extensive hyperparameter search, learning rate scheduling

### Medium-Risk Items:
1. **Baseline Reproduction**: Difficulty reproducing published results
   - **Mitigation**: Contact original authors, use multiple implementations

2. **Performance**: Not meeting target AUROC
   - **Mitigation**: Iterative model refinement, additional data sources

---

## Success Metrics

### Primary Metrics:
- **AUROC > 0.90** for cancer detection
- **Significant improvement** over baselines (p < 0.05)
- **Cross-modal synergy** demonstrated through ablation studies

### Secondary Metrics:
- **Tissue classification accuracy** > 0.80
- **Interpretability scores** for clinical relevance
- **Computational efficiency** < 1 hour per sample

---

## Resource Requirements

### Hardware:
- **GPU**: NVIDIA A100 or V100 (32GB+ VRAM)
- **CPU**: 32+ cores
- **RAM**: 256GB+
- **Storage**: 100TB+ (SSD preferred)

### Software:
- **Python 3.9+**
- **PyTorch 2.0+**
- **Snakemake**
- **Docker**

### External Dependencies:
- **NCBI dbGaP access**
- **EMMA study collaboration**
- **ENCODE data access**

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1 | 2 months | Data pipeline, signal extraction |
| 2 | 1 month | Model architecture, embeddings |
| 3 | 1 month | Pre-training, fine-tuning |
| 4 | 1 month | Baseline implementation, evaluation |
| 5 | 1 month | Interpretability, SHAP analysis |
| 6 | 1 month | Deployment, documentation |

**Total Duration**: 7 months
**Critical Path**: Data access → Signal extraction → Model training → Evaluation

---

## Next Steps

1. **Immediate Actions** (Week 1):
   - Set up development environment
   - Begin data access applications
   - Create project repository structure

2. **Week 2-4**:
   - Implement data retrieval scripts
   - Develop signal extraction pipeline
   - Set up baseline models

3. **Month 2**:
   - Complete data infrastructure
   - Begin model architecture development
   - Start pre-training data preparation

This action plan provides a comprehensive roadmap for implementing FragmentFusion, with clear milestones, deliverables, and risk mitigation strategies. The modular approach allows for parallel development and iterative refinement based on early results. 