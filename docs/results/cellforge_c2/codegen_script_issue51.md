C2 CHECKPOINT2 — EXACT GENERATED SCRIPT, posted BEFORE approval or ANY execution. First/only unchanged backend.run codegen turn completed0 at2026-10-31T17:33:15.314427UTC (131.256158250 wallseconds), no verifier/help/smoke/repair or generated-code execution. Approved planSHA228e4d5130b982da561fc0eb431342dff94eb362df48d9a46b910fdc4a9d8c4e and acceptance contract are unchanged. Script SHA256 **e3893320bd79c07efc47b49f50e499bf83fa15a30895fba9b3a4dcaac64b1b09**, 464lines,24797bytes, preserved byte-for-byte as result.raw.py and workspace/codegen/result.py. Delivery was strictJSON source decoded verbatim; rootASTsyntaxparse only, not an execution test. Static substantive review is pending; no training approval yet. Latest direct user instruction is resume same C2, no paid planning rerun, CPUtrain thenonecellforge_c2score ifconforming; anyCellForgefailurestop.

```python
"""CellForge CPU perturbation predictor.

Only --adata-path is read. Held-out perturbations are embedded from the acceptance
contract. Expression stays in the supplied log1p(counts per 10,000) units.
Internal validation uses training-file cells only; it is not an estimate of the
external unseen-perturbation benchmark. No external biological resources are used.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import re
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler


HELDOUT = [
    'AARS', 'ARHGAP22', 'ATF4', 'ATP5B', 'CCND3', 'DAD1', 'DARS', 'DHDDS',
    'DNAJC19', 'EIF2AK3', 'EIF2B3', 'EIF2B4', 'FARSB', 'HSPA5', 'HYOU1',
    'IDH3A', 'MARS', 'MRPL39', 'MTHFD1', 'OST4', 'PDIA6', 'PSMA1', 'PSMD4',
    'PTDSS1', 'QARS', 'SARS', 'SCYL1', 'SEC61B', 'SEC61G', 'SLC39A7', 'SOCS1',
    'SPCS2', 'SPCS3', 'SRP72', 'TIMM23', 'UFL1', 'XBP1', 'XRN1',
]
CONTROL_NAMES = {'control', 'ctrl', 'nt', 'ntc', 'non-targeting', 'non_targeting',
                 'nontargeting', 'negative_control', 'neg_control', 'scramble',
                 'scrambled', 'unperturbed', 'vehicle', 'dmso'}
N_GENES = 2055


def canonical(label):
    """Remove a control partner from common single-target CRISPR labels."""
    text = str(label).strip()
    if text.lower() in CONTROL_NAMES:
        return 'control'
    pieces = [p.strip() for p in re.split(r'[+;,]', text) if p.strip()]
    active = [p for p in pieces if p.lower() not in CONTROL_NAMES]
    return '+'.join(active) if active else 'control'


def targets(label):
    return [] if label == 'control' else label.split('+')


def matrix_rows(matrix, indices):
    block = matrix[indices]
    if hasattr(block, 'toarray'):
        block = block.toarray()
    return np.asarray(block, dtype=np.float32)


def select_column(obs, explicit, candidates, required=False):
    if explicit:
        if explicit not in obs:
            raise ValueError('Missing observation column: ' + explicit)
        return explicit
    for name in candidates:
        if name in obs:
            return name
    if required:
        raise ValueError('Specify --perturbation-key; no recognized perturbation column exists.')
    return None


def split_indices(labels, fraction, seed):
    """Stratify within training-file perturbations, retaining training controls."""
    rng = np.random.default_rng(seed)
    train, validation = [], []
    for label in sorted(set(labels)):
        rows = np.flatnonzero(labels == label)
        rng.shuffle(rows)
        n_val = min(len(rows) - 1, max(1, int(round(len(rows) * fraction)))) if len(rows) > 1 else 0
        validation.extend(rows[:n_val].tolist())
        train.extend(rows[n_val:].tolist())
    if not validation:
        raise ValueError('Internal validation requires at least one label with two cells.')
    return np.array(sorted(train)), np.array(sorted(validation))


class Preprocessor:
    """Fit imputation, control baselines and identity descriptors on training rows.

    Biological zeros are retained. Only nonfinite entries are imputed, using
    training gene means. Context-matched control means supply the unperturbed
    state because the screen does not contain paired before/after cells.
    """
    def __init__(self, adata, labels, contexts, train_indices):
        self.matrix = adata.X
        self.labels = labels
        self.contexts = contexts
        self.genes = np.asarray(adata.var_names.astype(str))
        self.gene_index = {name: i for i, name in enumerate(self.genes)}
        sums = np.zeros(N_GENES, dtype=np.float64)
        counts = np.zeros(N_GENES, dtype=np.int64)
        for start in range(0, len(train_indices), 512):
            values = matrix_rows(self.matrix, train_indices[start:start + 512])
            valid = np.isfinite(values)
            sums += np.where(valid, values, 0).sum(0, dtype=np.float64)
            counts += valid.sum(0)
        self.impute = np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0).astype(np.float32)
        controls = train_indices[labels[train_indices] == 'control']
        if not len(controls):
            raise ValueError('Training data must contain recognizable unperturbed controls.')
        self.global_control = self.mean(controls)
        self.context_baselines = {}
        for context in sorted(set(contexts[controls])):
            indices = controls[contexts[controls] == context]
            self.context_baselines[context] = self.mean(indices)
        self.context_vocab = {c: i + 1 for i, c in enumerate(sorted(set(contexts[train_indices])))}
        self.prediction_contexts, self.prediction_weights = np.unique(contexts[controls], return_counts=True)
        self.prediction_weights = self.prediction_weights.astype(np.float64)
        self.prediction_weights /= self.prediction_weights.sum()
        self.descriptors = {}
        # Coexpression descriptors let a panel gene be represented even when its
        # perturbation has no training cells. No held-out response is consulted.
        all_targets = sorted({t for p in list(labels[train_indices]) + HELDOUT for t in targets(p)})
        available = [t for t in all_targets if t in self.gene_index]
        self.correlations = {}
        if available:
            gene_sum = np.zeros(N_GENES, dtype=np.float64)
            gene_square = np.zeros(N_GENES, dtype=np.float64)
            cross = np.zeros((len(available), N_GENES), dtype=np.float64)
            target_sum = np.zeros(len(available), dtype=np.float64)
            target_square = np.zeros(len(available), dtype=np.float64)
            cols = [self.gene_index[t] for t in available]
            for start in range(0, len(train_indices), 512):
                values = self.rows(train_indices[start:start + 512]).astype(np.float64)
                selected = values[:, cols]
                gene_sum += values.sum(0)
                gene_square += np.square(values).sum(0)
                target_sum += selected.sum(0)
                target_square += np.square(selected).sum(0)
                cross += selected.T @ values
            n = len(train_indices)
            covariance = cross - target_sum[:, None] * gene_sum[None, :] / n
            variance = np.maximum(gene_square - gene_sum ** 2 / n, 0)
            target_variance = np.maximum(target_square - target_sum ** 2 / n, 0)
            denominator = np.sqrt(target_variance[:, None] * variance[None, :])
            corr = np.divide(covariance, denominator, out=np.zeros_like(covariance), where=denominator > 1e-12)
            self.correlations = {t: np.clip(corr[i], -1, 1).astype(np.float32) for i, t in enumerate(available)}

    def rows(self, indices):
        values = matrix_rows(self.matrix, indices)
        return np.where(np.isfinite(values), values, self.impute).astype(np.float32)

    def mean(self, indices):
        total = np.zeros(N_GENES, dtype=np.float64)
        for start in range(0, len(indices), 512):
            total += self.rows(indices[start:start + 512]).sum(0, dtype=np.float64)
        return (total / len(indices)).astype(np.float32)

    def baseline(self, context):
        return self.context_baselines.get(context, self.global_control)

    def descriptor(self, label):
        if label not in self.descriptors:
            vector = np.zeros(N_GENES, dtype=np.float32)
            for target in targets(label):
                if target in self.correlations:
                    vector += self.correlations[target]
                else:
                    # An absent panel target has no measured molecular features.
                    # Stable character features preserve identity without claiming
                    # access to sequence, pathways, or a pretrained resource.
                    padded = '^' + target.upper() + '$'
                    fragments = [padded[i:i + k] for k in (2, 3) for i in range(max(0, len(padded) - k + 1))]
                    for fragment in fragments:
                        digest = hashlib.sha256(fragment.encode('utf8')).digest()
                        vector[int.from_bytes(digest[:4], 'little') % N_GENES] += 1 if digest[4] % 2 else -1
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector /= norm
            self.descriptors[label] = vector
        return self.descriptors[label]


class CellDataset(Dataset):
    def __init__(self, prep, indices, classes):
        self.prep, self.indices, self.classes = prep, np.asarray(indices), classes

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, item):
        i = int(self.indices[item])
        context, label = self.prep.contexts[i], self.prep.labels[i]
        target = self.prep.rows([i])[0]
        identity = np.zeros(len(self.classes), dtype=np.float32)
        for gene in targets(label):
            if gene in self.classes:
                identity[self.classes[gene]] = 1
        return (self.prep.baseline(context).copy(), self.prep.descriptor(label).copy(),
                np.int64(self.prep.context_vocab.get(context, 0)), target, identity)


class PerturbationModel(nn.Module):
    """Approved 4-layer, 8-head, 512-dimensional transformer architecture.

    Contiguous expression patches tokenize the complete fixed panel, avoiding
    quadratic attention over thousands of scalar tokens on CPU. No gene is
    selected away, renormalized, or removed. Context is an additional token.
    """
    def __init__(self, n_contexts, n_perturbations):
        super().__init__()
        self.patch_width = 64
        self.n_patches = math.ceil(N_GENES / self.patch_width)
        self.expression_embedding = nn.Linear(self.patch_width, 512)
        self.position = nn.Parameter(torch.empty(1, self.n_patches, 512))
        nn.init.normal_(self.position, std=0.02)
        self.context_embedding = nn.Embedding(n_contexts + 1, 512, padding_idx=0)
        layer = nn.TransformerEncoderLayer(d_model=512, nhead=8, dim_feedforward=2048,
                                           dropout=0.1, activation='gelu', batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=4)
        self.perturbation_encoder = nn.Sequential(
            nn.Linear(N_GENES, 256), nn.SiLU(), nn.Linear(256, 128), nn.SiLU(),
            nn.Linear(128, 64), nn.SiLU())
        self.perturbation_projection = nn.Linear(64, 512)
        self.cross_attention = nn.MultiheadAttention(512, 8, dropout=0.1, batch_first=True)
        self.decoder = nn.Sequential(
            nn.Linear(512, 256), nn.SiLU(), nn.Linear(256, 512), nn.SiLU(),
            nn.Linear(512, 1024), nn.SiLU())
        self.expression_output = nn.Linear(1024, N_GENES)
        self.perturbation_output = nn.Linear(512, n_perturbations)

    def forward(self, baseline, perturbation, context):
        padding = self.n_patches * self.patch_width - N_GENES
        patches = nn.functional.pad(baseline, (0, padding)).reshape(-1, self.n_patches, self.patch_width)
        expression = self.expression_embedding(patches) + self.position
        context_token = self.context_embedding(context).unsqueeze(1)
        encoded = self.encoder(torch.cat([context_token, expression], dim=1))
        query = self.perturbation_projection(self.perturbation_encoder(perturbation)).unsqueeze(1)
        attended, _ = self.cross_attention(query, encoded, encoded, need_weights=False)
        latent = (attended + query).squeeze(1)
        # Predict a response relative to the biologically matched control state.
        predicted = baseline + self.expression_output(self.decoder(latent))
        return predicted, self.perturbation_output(latent)


def evaluate(model, loader):
    model.eval()
    squared_error = absolute_sum = square_sum = prediction_sum = prediction_square = cross = 0.0
    bce_sum = 0.0
    n_values = n_cells = 0
    with torch.no_grad():
        for baseline, descriptor, context, truth, identity in loader:
            predicted, logits = model(baseline, descriptor, context)
            bce_sum += nn.functional.binary_cross_entropy_with_logits(logits, identity).item() * len(truth)
            p, y = predicted.double(), truth.double()
            squared_error += torch.square(p - y).sum().item()
            absolute_sum += y.sum().item()
            square_sum += torch.square(y).sum().item()
            prediction_sum += p.sum().item()
            prediction_square += torch.square(p).sum().item()
            cross += (p * y).sum().item()
            n_values += y.numel()
            n_cells += len(y)
    if not n_cells:
        raise ValueError('Validation loader is empty.')
    mse = squared_error / n_values
    variance_y = max(0.0, square_sum - absolute_sum ** 2 / n_values)
    variance_p = max(0.0, prediction_square - prediction_sum ** 2 / n_values)
    denominator = math.sqrt(variance_y * variance_p)
    pcc = (cross - absolute_sum * prediction_sum / n_values) / denominator if denominator > 0 else None
    r2 = 1 - squared_error / variance_y if variance_y > 0 else None
    bce = bce_sum / n_cells
    return {'MSE': mse, 'PCC': pcc, 'R2': r2, 'perturbation_BCE': bce,
            'loss': mse + bce, 'n_cells': n_cells}


def train(model, prep, train_indices, val_indices, classes, args):
    train_dataset = CellDataset(prep, train_indices, classes)
    val_dataset = CellDataset(prep, val_indices, classes)
    labels, counts = np.unique(prep.labels[train_indices], return_counts=True)
    frequency = dict(zip(labels.tolist(), counts.tolist()))
    weights = torch.as_tensor([1.0 / frequency[prep.labels[i]] for i in train_indices], dtype=torch.double)
    generator = torch.Generator().manual_seed(args.seed)
    # Equal expected contribution per perturbation addresses screen imbalance.
    sampler = WeightedRandomSampler(weights, len(train_dataset), replacement=True, generator=generator)
    loader = DataLoader(train_dataset, batch_size=64, sampler=sampler, num_workers=0)
    validation = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0003, weight_decay=0.01)
    # T_0 specifies a cosine warm-restart period, rather than a T_max schedule.
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, eta_min=1e-6)
    best_state, best_loss, stale = None, float('inf'), 0
    history = []
    for epoch in range(args.epochs):
        model.train()
        total = 0.0
        seen = 0
        for baseline, descriptor, context, truth, identity in loader:
            optimizer.zero_grad(set_to_none=True)
            predicted, logits = model(baseline, descriptor, context)
            reconstruction = nn.functional.mse_loss(predicted, truth)
            perturbation = nn.functional.binary_cross_entropy_with_logits(logits, identity)
            loss = reconstruction + perturbation
            if not torch.isfinite(loss):
                raise FloatingPointError('Nonfinite training loss; inspect supplied expression values.')
            loss.backward()
            norm = nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            if not torch.isfinite(norm):
                raise FloatingPointError('Nonfinite training gradient.')
            optimizer.step()
            total += loss.item() * len(truth)
            seen += len(truth)
        scheduler.step(epoch + 1)
        metrics = evaluate(model, validation)
        if not math.isfinite(metrics['loss']):
            raise FloatingPointError('Nonfinite validation loss.')
        record = {'epoch': epoch + 1, 'training_loss': total / seen, **metrics}
        history.append(record)
        print(json.dumps(record, allow_nan=False), flush=True)
        if metrics['loss'] < best_loss - 0.0001:
            best_loss, stale = metrics['loss'], 0
            best_state = copy.deepcopy(model.state_dict())
            if args.checkpoint_out:
                destination = Path(args.checkpoint_out)
                destination.parent.mkdir(parents=True, exist_ok=True)
                torch.save({'model_state_dict': best_state, 'epoch': epoch + 1,
                            'genes': prep.genes.tolist(), 'perturbation_classes': classes,
                            'context_vocab': prep.context_vocab, 'seed': args.seed,
                            'imputation': prep.impute, 'global_control': prep.global_control,
                            'context_baselines': prep.context_baselines,
                            'descriptors': {p: prep.descriptor(p) for p in sorted(set(prep.labels.tolist() + HELDOUT))},
                            'prediction_contexts': prep.prediction_contexts,
                            'prediction_weights': prep.prediction_weights}, destination)
        else:
            stale += 1
            if stale >= 15:
                break
    if best_state is None:
        raise RuntimeError('Training did not produce a valid checkpoint.')
    model.load_state_dict(best_state)
    return evaluate(model, validation), history


def predict_heldout(model, prep):
    """Marginalize predicted means over training-control cell contexts only."""
    model.eval()
    means = np.zeros((len(HELDOUT), N_GENES), dtype=np.float64)
    with torch.no_grad():
        for context, weight in zip(prep.prediction_contexts, prep.prediction_weights):
            baseline = torch.from_numpy(np.repeat(prep.baseline(context)[None, :], len(HELDOUT), axis=0))
            descriptors = torch.from_numpy(np.stack([prep.descriptor(p) for p in HELDOUT]))
            contexts = torch.full((len(HELDOUT),), prep.context_vocab.get(context, 0), dtype=torch.long)
            predicted, _ = model(baseline, descriptors, contexts)
            means += float(weight) * predicted.numpy().astype(np.float64)
    means = means.astype(np.float32)
    if means.shape != (38, N_GENES) or not np.isfinite(means).all():
        raise FloatingPointError('Predictions must be a finite 38 by 2055 array.')
    return means


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_path_positional', nargs='?')
    parser.add_argument('--adata-path', '--adata_path', '--data_path', '--data', dest='adata_path')
    parser.add_argument('--predictions-out', default='predictions.npz')
    parser.add_argument('--output-metrics', '--metrics-path', '--output', dest='metrics_path')
    parser.add_argument('--checkpoint-out', default='checkpoint.pt')
    parser.add_argument('--perturbation-key')
    parser.add_argument('--cell-type-key')
    parser.add_argument('--batch-key')
    parser.add_argument('--control-label', action='append', default=[], help='Exact additional control label; repeat as needed.')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    if args.adata_path and args.data_path_positional and args.adata_path != args.data_path_positional:
        parser.error('Conflicting training data paths.')
    args.adata_path = args.adata_path or args.data_path_positional
    if not args.adata_path:
        parser.error('--adata-path is required.')
    if args.epochs < 1 or args.threads < 1:
        parser.error('--epochs and --threads must be positive.')
    # External validation paths are intentionally unsupported: the acceptance
    # contract authorizes reading only the supplied training AnnData file.
    return args


def main():
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.threads)
    torch.use_deterministic_algorithms(True)
    try:
        import anndata
    except ImportError as exc:
        raise RuntimeError('AnnData must already be installed; no dependencies are downloaded.') from exc
    input_path = Path(args.adata_path)
    # Prevent accidental destruction of the sole authorized data source.
    outputs = [args.predictions_out, args.checkpoint_out, args.metrics_path]
    resolved_outputs = [Path(p).resolve() for p in outputs if p]
    if input_path.resolve() in resolved_outputs or len(set(resolved_outputs)) != len(resolved_outputs):
        raise ValueError('Input, prediction, checkpoint and metrics paths must be distinct.')
    adata = anndata.read_h5ad(input_path)
    if adata.n_vars != N_GENES or not adata.var_names.is_unique:
        raise ValueError('Expected exactly 2055 uniquely named genes in the supplied order.')
    if adata.n_obs < 3:
        raise ValueError('Too few cells for training and internal validation.')
    perturbation_key = select_column(adata.obs, args.perturbation_key,
                                    ['perturbation', 'gene', 'target_gene', 'gene_target', 'condition', 'target', 'guide_target'], True)
    if adata.obs[perturbation_key].isna().any():
        raise ValueError('Missing perturbation labels are not valid control annotations.')
    labels = np.array([canonical(v) for v in adata.obs[perturbation_key]], dtype=str)
    explicit_controls = {str(v).strip() for v in args.control_label}
    if explicit_controls:
        labels = np.array(['control' if str(raw).strip() in explicit_controls else label
                           for raw, label in zip(adata.obs[perturbation_key], labels)], dtype=str)
    # The contract guarantees these targets have no training cells. Fail rather
    # than silently train on a mislabeled or incorrectly supplied screen.
    overlap = sorted({t for label in labels for t in targets(label)} & set(HELDOUT))
    if overlap:
        raise ValueError('Held-out perturbations found in training annotations: ' + ', '.join(overlap))
    cell_key = select_column(adata.obs, args.cell_type_key, ['cell_type', 'celltype', 'cell_line'])
    batch_key = select_column(adata.obs, args.batch_key, ['batch', 'batch_id', 'experiment'])
    cell_values = adata.obs[cell_key].fillna('unknown').astype(str).to_numpy() if cell_key else np.repeat('K562', adata.n_obs)
    batch_values = adata.obs[batch_key].fillna('unknown').astype(str).to_numpy() if batch_key else np.repeat('default', adata.n_obs)
    # A JSON tuple prevents collisions between cell type and experimental batch.
    contexts = np.array([json.dumps([c, b]) for c, b in zip(cell_values, batch_values)])
    train_indices, val_indices = split_indices(labels, 0.1, args.seed)
    prep = Preprocessor(adata, labels, contexts, train_indices)
    classes = {name: i for i, name in enumerate(sorted({t for p in labels[train_indices] for t in targets(p)}))}
    if not classes:
        raise ValueError('At least one non-control training perturbation is required.')
    model = PerturbationModel(len(prep.context_vocab), len(classes)).cpu()
    metrics, history = train(model, prep, train_indices, val_indices, classes, args)
    means = predict_heldout(model, prep)
    destination = Path(args.predictions_out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Using a file object preserves the exact requested output filename.
    with destination.open('wb') as handle:
        np.savez_compressed(handle, perts=np.asarray(HELDOUT, dtype=str), means=means, genes=prep.genes.astype(str))
    report = {'seed': args.seed, 'device': 'cpu', 'validation_source': 'stratified internal training-file split',
              'T01': metrics, 'T02': {'status': 'predictions generated; external held-out truth not accessed',
                                    'n_perturbations': len(HELDOUT), 'metrics': None},
              'n_training_cells': len(train_indices), 'n_validation_cells': len(val_indices),
              'genes': N_GENES, 'epochs_completed': len(history),
              'unmeasured_heldout_targets': [p for p in HELDOUT if p not in prep.gene_index],
              'biological_validation': {'TF_masking': 'not evaluated; no approved TF annotation supplied',
                                        'pathway_enrichment': 'not evaluated; no approved pathway annotation supplied',
                                        'UMAP': 'not used in benchmark prediction or evaluation'},
              'history': history}
    if args.metrics_path:
        path = Path(args.metrics_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf8') as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
    print(json.dumps({'predictions_out': str(destination), 'shape': list(means.shape), 'validation': metrics}, allow_nan=False), flush=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, FloatingPointError) as exc:
        raise SystemExit('CellForge error: ' + str(exc)) from exc

```

