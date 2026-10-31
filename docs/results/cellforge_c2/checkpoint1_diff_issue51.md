C2 CHECKPOINT1 EXACT DIFF, posted BEFORE operator approval. CandidateJSON SHA256 **228e4d5130b982da561fc0eb431342dff94eb362df48d9a46b910fdc4a9d8c4e**. This JSON—not Markdown—is what the authorized backend.run controller will consume. The unchanged originalJSON+MD remain preserved.

Only dated-note edits: QC/filtering/renormalization/log1p/regression/Harmony replaced by the exact sentence; dose/drug-class/curriculum/dose-loss and unsupported pathway priors removed; CPUdevice=cpu replaces GPU placement. Same narrow removals cover instruction-bearing diagram/module copies and both independent task_wise_plan.design_refs copies. Highly-variable-gene filtering and input scaling are removed under the fixed-panel/as-given rule; PCA, generic GNN options, GO/time-point labels, descriptive pathway evaluation/outputs/future extensions and other nonlisted content are retained. Those retained generic labels do not authorize unavailable inputs or extra components; any script requiring them will fail checkpoint2, not be repaired.

Protected comparison: all3 model_architecture subtrees and all3 training_strategy subtrees are EXACTLY EQUAL to rawJSON; framework/dependencies/code_structure/RAM/storage unchanged. AdamWlr0.0003/wd0.01, cosineT0=10/eta_min1e-6, batch64/clip1/earlystop15/minDelta0.0001 preserved; reconstructionMSE and perturbationBCE preserved. No epoch count invented, no component added. Explicit37-operation replay reproduces the candidate exactly; no unrecorded semantic edit. Source-only independent scope review agrees remaining generic labels alone do not force rejection; substantive checkpoint2 review remains necessary.

```diff
diff --git a/docs/results/cellforge_c2/raw_planning/plans/cellforge_input/research_plan_20261030_141205.json b/docs/results/cellforge_c2/checkpoint1_candidate.json
index 9c1343d..d112d3f 100644
--- a/docs/results/cellforge_c2/raw_planning/plans/cellforge_input/research_plan_20261030_141205.json
+++ b/docs/results/cellforge_c2/checkpoint1_candidate.json
@@ -35,34 +35,7 @@
     }
   },
   "data_processing": {
-    "quality_control": {
-      "cell_filtering": {
-        "min_genes": 200,
-        "max_genes": 6000,
-        "min_counts": 1000,
-        "max_counts": 50000,
-        "max_mito_percent": 20
-      },
-      "gene_filtering": {
-        "min_cells": 3,
-        "min_counts": 10
-      }
-    },
-    "normalization": {
-      "method": "log1p",
-      "target_sum": 10000,
-      "regression_vars": [
-        "total_counts",
-        "pct_counts_mt"
-      ]
-    },
-    "batch_correction": {
-      "method": "harmony",
-      "parameters": {
-        "theta": 2,
-        "max_iterations": 20
-      }
-    }
+    "input": "The input is already normalised (counts per 10,000, log1p) on a fixed panel of 2,055 genes; use it as given."
   },
   "training_strategy": {
     "optimizer": {
@@ -87,16 +60,15 @@
   "evaluation_metrics": {
     "loss_functions": {
       "reconstruction": "mse",
-      "perturbation": "bce",
-      "biological": "pathway_consistency"
+      "perturbation": "bce"
     }
   },
   "implementation_details": {
     "framework": "PyTorch",
     "hardware_requirements": {
-      "gpu": "NVIDIA GPU with 8GB+ VRAM",
       "ram": "32GB+ system RAM",
-      "storage": "100GB+ SSD"
+      "storage": "100GB+ SSD",
+      "device": "cpu"
     },
     "dependencies": [
       "torch>=1.12.0",
@@ -118,11 +90,6 @@
         "validation": "Ablation study (masking key TFs)",
         "biological_basis": "Central dogma of molecular biology"
       },
-      "dose_response_continuity": {
-        "assumption": "Dose-response continuity",
-        "validation": "Dose interpolation experiments",
-        "biological_basis": "Ligand-receptor binding kinetics"
-      },
       "pathway_modularity": {
         "assumption": "Pathway modularity",
         "validation": "Pathway enrichment analysis",
@@ -134,62 +101,30 @@
         "biological_basis": "Waddington epigenetic landscape concept"
       }
     },
-    "adaptive_mechanisms": {
-      "dose_specific_attention": {
-        "description": "Higher attention weights to stress pathways at toxic doses",
-        "implementation": "Focus on growth signaling at therapeutic doses"
-      },
-      "cell_type_gating": {
-        "description": "Cell-type specific pathway modulation",
-        "implementation": "Suppress irrelevant pathways based on cell type"
-      },
-      "chemical_class_priors": {
-        "description": "Initialize embeddings based on chemical class",
-        "implementation": "Set initial weights based on known mechanisms"
-      }
-    }
+    "adaptive_mechanisms": {}
   },
   "computational_optimization": {
-    "training_techniques": {
-      "progressive_dose_sampling": {
-        "description": "Gradually increase dose range during training",
-        "implementation": {
-          "epoch_0_10": "uniform(0, 1μM)",
-          "epoch_10_20": "log_normal(1μM-10μM)",
-          "epoch_20+": "full_range(0-100μM)"
-        }
-      }
-    },
-    "regularization_methods": {
-      "pathway_sparsity": {
-        "type": "l1",
-        "lambda": 0.01,
-        "target": "pathway_weights"
-      },
-      "dose_consistency": {
-        "type": "custom",
-        "formula": "L_consist = E[||f(x,d1) - f(f(x,d1),d2-d1)||^2]"
-      }
-    },
+    "training_techniques": {},
+    "regularization_methods": {},
     "parallelization": {
       "gene_cluster_parallelism": {
         "chr1": {
-          "gpu": "GPU0",
           "genes": [
             "EGFR",
             "MYC"
-          ]
+          ],
+          "device": "cpu"
         },
         "chr17": {
-          "gpu": "GPU1",
           "genes": [
             "TP53",
             "BRCA1"
-          ]
+          ],
+          "device": "cpu"
         },
         "others": {
-          "gpu": "GPU2",
-          "genes": "Housekeeping"
+          "genes": "Housekeeping",
+          "device": "cpu"
         }
       }
     }
@@ -201,8 +136,7 @@
         "solution": "Advanced sampling and weighting techniques"
       },
       "batch_effects": {
-        "challenge": "Batch effects between experiments",
-        "solution": "Harmony integration and batch correction"
+        "challenge": "Batch effects between experiments"
       },
       "technical_noise": {
         "challenge": "Missing values and technical noise",
@@ -272,7 +206,7 @@
     "system_overview": {
       "title": "Research Framework Architecture",
       "description": "Complete research framework for biological perturbation analysis using single-cell data",
-      "mermaid_code": "graph TD\n    %% Data Input Layer\n    subgraph InputLayer [\"📊 Data Input Layer\"]\n        RawData[\"Raw Single-cell Data<br/>• Gene expression matrices<br/>• Cell metadata<br/>• Perturbation information\"]\n        Metadata[\"Metadata<br/>• Cell types<br/>• Batch information<br/>• Experimental conditions\"]\n    end\n\n    %% Data Processing Layer\n    subgraph ProcessingLayer [\"🔧 Data Processing Layer\"]\n        QC[\"Quality Control<br/>• Cell filtering<br/>• Gene filtering<br/>• Doublet detection\"]\n        Norm[\"Normalization<br/>• Count normalization<br/>• Log transformation<br/>• Batch correction\"]\n        Feature[\"Feature Selection<br/>• Highly variable genes<br/>• Dimensionality reduction<br/>• Feature engineering\"]\n    end\n\n    %% Model Architecture Layer\n    subgraph ModelLayer [\"🧠 Model Architecture Layer\"]\n        Encoder[\"Encoder<br/>• Transformer/GNN<br/>• Gene embedding<br/>• Cell type embedding\"]\n        Decoder[\"Decoder<br/>• Conditional generation<br/>• Perturbation prediction<br/>• Response modeling\"]\n        Constraints[\"Biological Constraints<br/>• Pathway information<br/>• Network structure<br/>• Cell type specificity\"]\n    end\n\n    %% Training Layer\n    subgraph TrainingLayer [\"🎯 Training Layer\"]\n        Optimizer[\"Optimizer<br/>• Adam/AdamW<br/>• Learning rate scheduling<br/>• Gradient clipping\"]\n        Loss[\"Loss Functions<br/>• Reconstruction loss<br/>• Biological constraints<br/>• Regularization\"]\n        Validation[\"Validation<br/>• Cross-validation<br/>• Early stopping<br/>• Model checkpointing\"]\n    end\n\n    %% Evaluation Layer\n    subgraph EvaluationLayer [\"📈 Evaluation Layer\"]\n        TechMetrics[\"Technical Metrics<br/>• MSE, R²<br/>• Pearson correlation<br/>• AUROC\"]\n        BioMetrics[\"Biological Metrics<br/>• Pathway enrichment<br/>• Network consistency<br/>• Cell type specificity\"]\n        Validation[\"Biological Validation<br/>• Experimental validation<br/>• Literature comparison<br/>• Expert assessment\"]\n    end\n\n    %% Output Layer\n    subgraph OutputLayer [\"📋 Output Layer\"]\n        Predictions[\"Predictions<br/>• Gene expression changes<br/>• Cell state transitions<br/>• Pathway activities\"]\n        Insights[\"Biological Insights<br/>• Mechanism of action<br/>• Drug targets<br/>• Biomarkers\"]\n        Applications[\"Applications<br/>• Drug discovery<br/>• Precision medicine<br/>• Biomarker discovery\"]\n    end\n\n    %% Data Flow Connections\n    RawData --> QC\n    Metadata --> QC\n    QC --> Norm\n    Norm --> Feature\n    Feature --> Encoder\n    Encoder --> Decoder\n    Constraints --> Decoder\n    Decoder --> Optimizer\n    Optimizer --> Loss\n    Loss --> Validation\n    Validation --> TechMetrics\n    TechMetrics --> BioMetrics\n    BioMetrics --> Validation\n    Validation --> Predictions\n    Predictions --> Insights\n    Insights --> Applications\n\n    %% Styling\n    classDef inputStyle fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n    classDef processingStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n    classDef modelStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n    classDef trainingStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px\n    classDef evaluationStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px\n    classDef outputStyle fill:#e0f2f1,stroke:#004d40,stroke-width:2px\n    classDef subgraphStyle fill:#fafafa,stroke:#666,stroke-width:1px\n\n    class RawData,Metadata inputStyle\n    class QC,Norm,Feature processingStyle\n    class Encoder,Decoder,Constraints modelStyle\n    class Optimizer,Loss,Validation trainingStyle\n    class TechMetrics,BioMetrics,Validation evaluationStyle\n    class Predictions,Insights,Applications outputStyle\n    class InputLayer,ProcessingLayer,ModelLayer,TrainingLayer,EvaluationLayer,OutputLayer subgraphStyle",
+      "mermaid_code": "graph TD\n    %% Data Input Layer\n    subgraph InputLayer [\"📊 Data Input Layer\"]\n        RawData[\"Raw Single-cell Data<br/>• Gene expression matrices<br/>• Cell metadata<br/>• Perturbation information\"]\n        Metadata[\"Metadata<br/>• Cell types<br/>• Batch information<br/>• Experimental conditions\"]\n    end\n\n    %% Data Processing Layer\n    subgraph ProcessingLayer [\"🔧 Data Processing Layer\"]\n        Norm[\"The input is already normalised (counts per 10,000, log1p) on a fixed panel of 2,055 genes; use it as given.\"]\n        Feature[\"Feature Selection<br/>• Dimensionality reduction<br/>• Feature engineering\"]\n    end\n\n    %% Model Architecture Layer\n    subgraph ModelLayer [\"🧠 Model Architecture Layer\"]\n        Encoder[\"Encoder<br/>• Transformer/GNN<br/>• Gene embedding<br/>• Cell type embedding\"]\n        Decoder[\"Decoder<br/>• Conditional generation<br/>• Perturbation prediction<br/>• Response modeling\"]\n        Constraints[\"Biological Constraints<br/>• Network structure<br/>• Cell type specificity\"]\n    end\n\n    %% Training Layer\n    subgraph TrainingLayer [\"🎯 Training Layer\"]\n        Optimizer[\"Optimizer<br/>• Adam/AdamW<br/>• Learning rate scheduling<br/>• Gradient clipping\"]\n        Loss[\"Loss Functions<br/>• Reconstruction loss<br/>• Biological constraints<br/>• Regularization\"]\n        Validation[\"Validation<br/>• Cross-validation<br/>• Early stopping<br/>• Model checkpointing\"]\n    end\n\n    %% Evaluation Layer\n    subgraph EvaluationLayer [\"📈 Evaluation Layer\"]\n        TechMetrics[\"Technical Metrics<br/>• MSE, R²<br/>• Pearson correlation<br/>• AUROC\"]\n        BioMetrics[\"Biological Metrics<br/>• Pathway enrichment<br/>• Network consistency<br/>• Cell type specificity\"]\n        Validation[\"Biological Validation<br/>• Experimental validation<br/>• Literature comparison<br/>• Expert assessment\"]\n    end\n\n    %% Output Layer\n    subgraph OutputLayer [\"📋 Output Layer\"]\n        Predictions[\"Predictions<br/>• Gene expression changes<br/>• Cell state transitions<br/>• Pathway activities\"]\n        Insights[\"Biological Insights<br/>• Mechanism of action<br/>• Drug targets<br/>• Biomarkers\"]\n        Applications[\"Applications<br/>• Drug discovery<br/>• Precision medicine<br/>• Biomarker discovery\"]\n    end\n\n    %% Data Flow Connections\n    RawData --> Norm\n    Metadata --> Norm\n    Norm --> Feature\n    Feature --> Encoder\n    Encoder --> Decoder\n    Constraints --> Decoder\n    Decoder --> Optimizer\n    Optimizer --> Loss\n    Loss --> Validation\n    Validation --> TechMetrics\n    TechMetrics --> BioMetrics\n    BioMetrics --> Validation\n    Validation --> Predictions\n    Predictions --> Insights\n    Insights --> Applications\n\n    %% Styling\n    classDef inputStyle fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n    classDef processingStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n    classDef modelStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n    classDef trainingStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px\n    classDef evaluationStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px\n    classDef outputStyle fill:#e0f2f1,stroke:#004d40,stroke-width:2px\n    classDef subgraphStyle fill:#fafafa,stroke:#666,stroke-width:1px\n\n    class RawData,Metadata inputStyle\n    class Norm,Feature processingStyle\n    class Encoder,Decoder,Constraints modelStyle\n    class Optimizer,Loss,Validation trainingStyle\n    class TechMetrics,BioMetrics,Validation evaluationStyle\n    class Predictions,Insights,Applications outputStyle\n    class InputLayer,ProcessingLayer,ModelLayer,TrainingLayer,EvaluationLayer,OutputLayer subgraphStyle",
       "modules": {
         "data_input_layer": {
           "name": "Data Input Layer",
@@ -306,33 +240,13 @@
         },
         "data_processing_layer": {
           "name": "Data Processing Layer",
-          "description": "Quality control, normalization, and feature selection",
+          "description": "The input is already normalised (counts per 10,000, log1p) on a fixed panel of 2,055 genes; use it as given.",
           "components": {
-            "quality_control": {
-              "name": "Quality Control",
-              "description": "Cell filtering, gene filtering, and doublet detection",
-              "methods": [
-                "scanpy.pp.filter_cells",
-                "scanpy.pp.filter_genes",
-                "scanpy.pp.scrublet"
-              ]
-            },
-            "normalization": {
-              "name": "Normalization",
-              "description": "Count normalization, log transformation, and batch correction",
-              "methods": [
-                "scanpy.pp.normalize_total",
-                "scanpy.pp.log1p",
-                "scanpy.pp.regress_out"
-              ]
-            },
             "feature_selection": {
               "name": "Feature Selection",
-              "description": "Highly variable genes, dimensionality reduction, and feature engineering",
+              "description": "Dimensionality reduction and feature engineering",
               "methods": [
-                "scanpy.pp.highly_variable_genes",
-                "scanpy.pp.pca",
-                "scanpy.pp.scale"
+                "scanpy.pp.pca"
               ]
             }
           }
@@ -371,10 +285,9 @@
             },
             "constraints": {
               "name": "Biological Constraints",
-              "description": "Integration of pathway information, network structure, and cell type specificity",
+              "description": "Integration of network structure and cell type specificity",
               "types": [
                 "gene_regulatory_networks",
-                "pathway_interactions",
                 "cell_type_specificity"
               ]
             }
@@ -492,18 +405,17 @@
     "detailed_architecture": {
       "title": "Detailed Component Architecture",
       "description": "Detailed view of encoder, decoder, training, and evaluation components",
-      "mermaid_code": "graph LR\n    %% Detailed Architecture Components\n    subgraph EncoderDetails [\"🔍 Encoder Details\"]\n        GeneEmbed[\"Gene Embedding<br/>• Positional encoding<br/>• Gene ontology<br/>• Pathway information\"]\n        CellEmbed[\"Cell Embedding<br/>• Cell type markers<br/>• State information<br/>• Batch effects\"]\n        Attention[\"Multi-head Attention<br/>• Gene-gene interactions<br/>• Cell-cell relationships<br/>• Perturbation effects\"]\n    end\n\n    subgraph DecoderDetails [\"🎯 Decoder Details\"]\n        Condition[\"Conditional Input<br/>• Perturbation type<br/>• Dose information<br/>• Time point\"]\n        Generation[\"Response Generation<br/>• Expression prediction<br/>• State transition<br/>• Pathway activation\"]\n        Output[\"Output Processing<br/>• Denormalization<br/>• Quality control<br/>• Biological validation\"]\n    end\n\n    subgraph TrainingDetails [\"⚙️ Training Details\"]\n        DataLoader[\"Data Loading<br/>• Batch sampling<br/>• Augmentation<br/>• Balancing\"]\n        Optimizer[\"Optimization<br/>• Adam optimizer<br/>• Learning rate decay<br/>• Weight decay\"]\n        Monitoring[\"Monitoring<br/>• Loss tracking<br/>• Gradient norms<br/>• Validation metrics\"]\n    end\n\n    subgraph EvaluationDetails [\"📊 Evaluation Details\"]\n        TechEval[\"Technical Evaluation<br/>• Reconstruction error<br/>• Prediction accuracy<br/>• Generalization\"]\n        BioEval[\"Biological Evaluation<br/>• Pathway enrichment<br/>• Network analysis<br/>• Literature validation\"]\n        Robustness[\"Robustness Tests<br/>• Cross-validation<br/>• Ablation studies<br/>• Sensitivity analysis\"]\n    end\n\n    %% Connections\n    GeneEmbed --> Attention\n    CellEmbed --> Attention\n    Attention --> Condition\n    Condition --> Generation\n    Generation --> Output\n    Output --> DataLoader\n    DataLoader --> Optimizer\n    Optimizer --> Monitoring\n    Monitoring --> TechEval\n    TechEval --> BioEval\n    BioEval --> Robustness\n\n    %% Styling\n    classDef encoderStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n    classDef decoderStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px\n    classDef trainingStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n    classDef evaluationStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px\n\n    class GeneEmbed,CellEmbed,Attention encoderStyle\n    class Condition,Generation,Output decoderStyle\n    class DataLoader,Optimizer,Monitoring trainingStyle\n    class TechEval,BioEval,Robustness evaluationStyle",
+      "mermaid_code": "graph LR\n    %% Detailed Architecture Components\n    subgraph EncoderDetails [\"🔍 Encoder Details\"]\n        GeneEmbed[\"Gene Embedding<br/>• Positional encoding<br/>• Gene ontology\"]\n        CellEmbed[\"Cell Embedding<br/>• Cell type markers<br/>• State information<br/>• Batch effects\"]\n        Attention[\"Multi-head Attention<br/>• Gene-gene interactions<br/>• Cell-cell relationships<br/>• Perturbation effects\"]\n    end\n\n    subgraph DecoderDetails [\"🎯 Decoder Details\"]\n        Condition[\"Conditional Input<br/>• Perturbation type<br/>• Time point\"]\n        Generation[\"Response Generation<br/>• Expression prediction<br/>• State transition<br/>• Pathway activation\"]\n        Output[\"Output Processing<br/>• Denormalization<br/>• Quality control<br/>• Biological validation\"]\n    end\n\n    subgraph TrainingDetails [\"⚙️ Training Details\"]\n        DataLoader[\"Data Loading<br/>• Batch sampling<br/>• Augmentation<br/>• Balancing\"]\n        Optimizer[\"Optimization<br/>• Adam optimizer<br/>• Learning rate decay<br/>• Weight decay\"]\n        Monitoring[\"Monitoring<br/>• Loss tracking<br/>• Gradient norms<br/>• Validation metrics\"]\n    end\n\n    subgraph EvaluationDetails [\"📊 Evaluation Details\"]\n        TechEval[\"Technical Evaluation<br/>• Reconstruction error<br/>• Prediction accuracy<br/>• Generalization\"]\n        BioEval[\"Biological Evaluation<br/>• Pathway enrichment<br/>• Network analysis<br/>• Literature validation\"]\n        Robustness[\"Robustness Tests<br/>• Cross-validation<br/>• Ablation studies<br/>• Sensitivity analysis\"]\n    end\n\n    %% Connections\n    GeneEmbed --> Attention\n    CellEmbed --> Attention\n    Attention --> Condition\n    Condition --> Generation\n    Generation --> Output\n    Output --> DataLoader\n    DataLoader --> Optimizer\n    Optimizer --> Monitoring\n    Monitoring --> TechEval\n    TechEval --> BioEval\n    BioEval --> Robustness\n\n    %% Styling\n    classDef encoderStyle fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n    classDef decoderStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px\n    classDef trainingStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n    classDef evaluationStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px\n\n    class GeneEmbed,CellEmbed,Attention encoderStyle\n    class Condition,Generation,Output decoderStyle\n    class DataLoader,Optimizer,Monitoring trainingStyle\n    class TechEval,BioEval,Robustness evaluationStyle",
       "components": {
         "encoder_details": {
           "name": "Encoder Details",
           "components": {
             "gene_embedding": {
               "name": "Gene Embedding",
-              "description": "Positional encoding, gene ontology, pathway information",
+              "description": "Positional encoding, gene ontology",
               "features": [
                 "positional_encoding",
-                "gene_ontology",
-                "pathway_information"
+                "gene_ontology"
               ]
             },
             "cell_embedding": {
@@ -531,10 +443,9 @@
           "components": {
             "condition": {
               "name": "Conditional Input",
-              "description": "Perturbation type, dose information, time point",
+              "description": "Perturbation type, time point",
               "features": [
                 "perturbation_type",
-                "dose_information",
                 "time_point"
               ]
             },
@@ -743,34 +654,7 @@
           }
         },
         "data_processing": {
-          "quality_control": {
-            "cell_filtering": {
-              "min_genes": 200,
-              "max_genes": 6000,
-              "min_counts": 1000,
-              "max_counts": 50000,
-              "max_mito_percent": 20
-            },
-            "gene_filtering": {
-              "min_cells": 3,
-              "min_counts": 10
-            }
-          },
-          "normalization": {
-            "method": "log1p",
-            "target_sum": 10000,
-            "regression_vars": [
-              "total_counts",
-              "pct_counts_mt"
-            ]
-          },
-          "batch_correction": {
-            "method": "harmony",
-            "parameters": {
-              "theta": 2,
-              "max_iterations": 20
-            }
-          }
+          "input": "The input is already normalised (counts per 10,000, log1p) on a fixed panel of 2,055 genes; use it as given."
         },
         "training_strategy": {
           "optimizer": {
@@ -795,9 +679,9 @@
         "implementation_details": {
           "framework": "PyTorch",
           "hardware_requirements": {
-            "gpu": "NVIDIA GPU with 8GB+ VRAM",
             "ram": "32GB+ system RAM",
-            "storage": "100GB+ SSD"
+            "storage": "100GB+ SSD",
+            "device": "cpu"
           },
           "dependencies": [
             "torch>=1.12.0",
@@ -891,34 +775,7 @@
           }
         },
         "data_processing": {
-          "quality_control": {
-            "cell_filtering": {
-              "min_genes": 200,
-              "max_genes": 6000,
-              "min_counts": 1000,
-              "max_counts": 50000,
-              "max_mito_percent": 20
-            },
-            "gene_filtering": {
-              "min_cells": 3,
-              "min_counts": 10
-            }
-          },
-          "normalization": {
-            "method": "log1p",
-            "target_sum": 10000,
-            "regression_vars": [
-              "total_counts",
-              "pct_counts_mt"
-            ]
-          },
-          "batch_correction": {
-            "method": "harmony",
-            "parameters": {
-              "theta": 2,
-              "max_iterations": 20
-            }
-          }
+          "input": "The input is already normalised (counts per 10,000, log1p) on a fixed panel of 2,055 genes; use it as given."
         },
         "training_strategy": {
           "optimizer": {
@@ -943,9 +800,9 @@
         "implementation_details": {
           "framework": "PyTorch",
           "hardware_requirements": {
-            "gpu": "NVIDIA GPU with 8GB+ VRAM",
             "ram": "32GB+ system RAM",
-            "storage": "100GB+ SSD"
+            "storage": "100GB+ SSD",
+            "device": "cpu"
           },
           "dependencies": [
             "torch>=1.12.0",
@@ -963,4 +820,4 @@
       }
     }
   ]
-}
\ No newline at end of file
+}

```

Protected subtree receipts:
```json
[
  {
    "path": [
      "model_architecture"
    ],
    "sha256": "316b4237b23b2fd790915bb8fde4fe46a942c9c650e6da5fedca39caaf3c55c7",
    "unchanged": true
  },
  {
    "path": [
      "training_strategy"
    ],
    "sha256": "2c939d189a38ae9aa81559a35d43a6b05b521ec960c9752c61ff69eb48b405f2",
    "unchanged": true
  },
  {
    "path": [
      "task_wise_plan",
      0,
      "design_refs",
      "model_architecture"
    ],
    "sha256": "316b4237b23b2fd790915bb8fde4fe46a942c9c650e6da5fedca39caaf3c55c7",
    "unchanged": true
  },
  {
    "path": [
      "task_wise_plan",
      0,
      "design_refs",
      "training_strategy"
    ],
    "sha256": "2c939d189a38ae9aa81559a35d43a6b05b521ec960c9752c61ff69eb48b405f2",
    "unchanged": true
  },
  {
    "path": [
      "task_wise_plan",
      1,
      "design_refs",
      "model_architecture"
    ],
    "sha256": "316b4237b23b2fd790915bb8fde4fe46a942c9c650e6da5fedca39caaf3c55c7",
    "unchanged": true
  },
  {
    "path": [
      "task_wise_plan",
      1,
      "design_refs",
      "training_strategy"
    ],
    "sha256": "2c939d189a38ae9aa81559a35d43a6b05b521ec960c9752c61ff69eb48b405f2",
    "unchanged": true
  }
]
```

Approval remains pending until after this post.
