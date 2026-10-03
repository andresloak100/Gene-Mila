import numpy as np
from genemila.features.api import Feature, FeatureContext, register

@register
class TFGatedCoexpressionE26(Feature):
    name = "tf_gated_coexpression_e26"
    version = 1
    description = "TF-gated co-expression: interaction of target's TF status with co-expression"
    rationale = "TF targets propagate knockouts along co-expression; non-TF targets mostly reflect shared drivers"
    inputs = ["control_cells"]
    params = {"zero_self": True}
    dim = 2

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        # Initialize output: (n_perts, n_genes, 2)
        out = np.zeros((len(perts), ctx.n_genes, 2))
        
        # Get transcription factors list
        tf_list = ctx.knowledge('transcription_factors')
        if tf_list is None:
            tf_list = []
        
        # Create a set for fast lookup
        tf_set = set(tf_list)
        
        # Get correlation matrix (n_genes, n_genes)
        corr_matrix = ctx.gene_corr
        
        for i, p in enumerate(perts):
            # Get target genes for this perturbation
            target_genes = ctx.target_genes(p)
            
            # Use the first target (should be single-gene targets in this dataset)
            if not target_genes:
                continue
            
            target_gene = target_genes[0]
            target_idx = ctx.gene_index.get(target_gene)
            if target_idx is None:
                continue
            
            # Get correlation row for this target
            target_corr = corr_matrix[target_idx, :].copy()
            
            # Zero self-correlation (the target gene itself)
            if params.get("zero_self", True):
                target_corr[target_idx] = 0.0
            
            # Check if target is a TF
            is_tf = 1.0 if target_gene in tf_set else 0.0
            
            # Compute the two gated versions
            tf_part = target_corr * is_tf
            nontf_part = target_corr * (1.0 - is_tf)
            
            # Assign to output
            out[i, :, 0] = tf_part
            out[i, :, 1] = nontf_part
        
        return out
