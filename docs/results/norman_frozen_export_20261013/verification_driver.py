#!/usr/bin/env python3
"""Root-controlled B1 saved-prediction reproduction; never score or refit.

Run only after the export full suite passes and the diagnostic run finishes.
Derive the own clone from this archived helper location. Pass --receipt explicitly.
All outputs go in a new directory under this own clone's ignored runs/, outside historical sources. Numeric/public
packages remain nontracked; only the data-free verification metadata is archived.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

WORKTREE = Path(__file__).resolve().parents[3]
RECEIPT_PIN = 'f0b2424676b559f9140c656bd8264649fb405144abf3f1c89115277de76341b9'
BASE = '076282c71b7c54fef47674b8797fda736eff6f01'
CORE_DIFF_PIN = 'a7267e73f6bea54c16de23d63f7fd2a78564f413d34a9adc7950dbb77910fdaf'
SELECTIONS = [('EXP_0681', 20000.0), ('EXP_0729', 0.00198), ('EXP_0519', 300.0)]
RTOL = 1e-6
ATOL = 1e-6
CORE_PATHS = ['genemila/features/__init__.py', 'genemila/features/api.py',
              'genemila/features/builtin.py', 'genemila/features/registry.py', 'genemila/pipeline.py']
sys.path.insert(0, str(WORKTREE))

import numpy as np
from genemila.frozen import export_ensemble, predict_ensemble, runtime_receipt, sha256


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def git_bytes(*args):
    return subprocess.run(['git', '--no-pager', *args], cwd=WORKTREE, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def core_audit(out):
    diff = git_bytes('diff', '--no-ext-diff', BASE, '--', 'genemila/features', 'genemila/pipeline.py')
    digest = hashlib.sha256(diff).hexdigest()
    if digest != CORE_DIFF_PIN:
        raise ValueError('core source diff changed after reviewed audit')
    (out / 'training_core_compatibility.diff').write_bytes(diff)
    sources = {}
    for path in CORE_PATHS:
        original = git_bytes('show', f'{BASE}:{path}')
        actual = (WORKTREE / path).read_bytes()
        sources[path] = {'training_sha256': hashlib.sha256(original).hexdigest(),
                         'current_sha256': hashlib.sha256(actual).hexdigest(),
                         'byte_identical': original == actual}
    for path in ('genemila/features/__init__.py', 'genemila/features/api.py', 'genemila/pipeline.py'):
        if not sources[path]['byte_identical']:
            raise ValueError('required original core implementation changed')
    old_builtin = git_bytes('show', f'{BASE}:genemila/features/builtin.py')
    if not (WORKTREE / 'genemila/features/builtin.py').read_bytes().startswith(old_builtin):
        raise ValueError('original builtin feature prefix changed')
    return {'training_commit': BASE, 'reviewed_diff_sha256': digest, 'sources': sources,
            'finding': 'API/pipeline/feature initializer identical; original three builtin formulas preserved; later additive helper/feature and registry constants added',
            'limit': 'core is not wholly byte-identical; frozen prediction reproduction is required'}


def comparison(a, b):
    if a.shape != b.shape or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError('saved/reproduced prediction shape or finiteness failure')
    difference = np.abs(a.astype(np.float64) - b.astype(np.float64))
    allowed = ATOL + RTOL * np.abs(b.astype(np.float64))
    return {'shape': list(a.shape), 'rtol': RTOL, 'atol': ATOL,
            'max_abs_difference': float(difference.max()),
            'mean_abs_difference': float(difference.mean()),
            'values_exceeding_tolerance': int((difference > allowed).sum()),
            'array_equal': bool(np.array_equal(a, b)),
            'passes_predeclared_tolerance': bool(np.allclose(a, b, rtol=RTOL, atol=ATOL))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True,
                        help='the unchanged PR13 frozen B1 receipt; its source SHA256 is fixed')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    receipt_path = args.receipt.resolve()
    receipt = json.loads(receipt_path.read_text())
    if sha256(receipt_path) != RECEIPT_PIN:
        raise ValueError('source receipt changed')
    runs = [Path(m['run_directory']).resolve() for m in receipt['frozen_members']]
    own_runs = WORKTREE / 'runs'
    if (out.exists() or own_runs.is_symlink() or out == own_runs.resolve() or
            not out.is_relative_to(own_runs.resolve()) or any(out.is_relative_to(run) for run in runs)):
        raise ValueError('verification output must be absent, strictly under this own clone runs/, and outside source runs')
    if os.environ.get('PYTHONHASHSEED') != '0':
        raise ValueError('start this fresh interpreter with PYTHONHASHSEED=0')
    out.mkdir(parents=True)
    config = {'created_utc': utc(), 'task': 'frozen_B1_saved_prediction_reproduction',
              'source_receipt': str(receipt_path), 'source_receipt_sha256': RECEIPT_PIN,
              'worktree': str(WORKTREE), 'worktree_head': git_bytes('rev-parse', 'HEAD').decode().strip(),
              'helper_sha256': sha256(Path(__file__)), 'runtime': runtime_receipt(),
              'selected_models': [{'experiment_id': name, 'alpha': alpha, 'weight': 1/3} for name, alpha in SELECTIONS],
              'comparison': {'rtol': RTOL, 'atol': ATOL, 'rule': 'all members and equal ensemble pass with exact condition and gene order'},
              'expected_full_grid_indices': [0, 1, 4],
              'inputs': 'original hash-pinned fitted models, public training context, feature source, and saved predictions only',
              'access': 'no private data, split files, test labels, oracle, summary scores, fitting or model selection',
              'predeclared_core_diff_sha256': CORE_DIFF_PIN,
              'output_directory': str(out)}
    # This immutable config is written before export, feature work, or prediction reads.
    write_json(out / 'config.json', config)
    (out / 'RUNNING').write_text(utc() + '\n')
    started = time.monotonic()
    summary = {'status': 'failed', 'started_utc': utc(), 'output_directory': str(out),
               'config_sha256': sha256(out / 'config.json'), 'member_comparisons': [],
               'no_scoring': True, 'scientific_gain': 'not evaluated; reproduction only'}
    try:
        summary['core_compatibility_audit'] = core_audit(out)
        source_members = receipt['frozen_members']
        if [(m['experiment_id'], m['selected_alpha']) for m in source_members] != SELECTIONS:
            raise ValueError('frozen member identity/alpha/order changed')
        if any(m['base_commit'] != BASE or abs(m['weight'] - 1/3) > 1e-12 for m in source_members):
            raise ValueError('frozen training commit or equal weight changed')
        package = out / 'package'
        manifest = export_ensemble(receipt_path, RECEIPT_PIN, SELECTIONS, package, trust_pickle=True)
        manifest_pin = sha256(package / 'manifest.json')
        summary['manifest_sha256'] = manifest_pin
        summary['anchor_sha256'] = manifest['anchor_sha256']
        summary['frozen_alpha_indices'] = [m['full_grid_index'] for m in manifest['members']]
        if summary['frozen_alpha_indices'] != [0, 1, 4]:
            raise ValueError('full alpha grid indices changed')
        expected_perts = manifest['anchor_perts']
        targets = json.loads((package / 'context/knowledge/targets.json').read_text())
        queries = {'schema_version': 1, 'queries': [
            {'condition_id': condition, 'target_genes': targets[condition]} for condition in expected_perts]}
        query_path = out / 'original_target_only_queries.json'
        write_json(query_path, queries)
        prediction_out = out / 'reproduced'
        prediction_receipt = predict_ensemble(package, manifest_pin, query_path, prediction_out)
        summary['prediction_receipt_sha256'] = sha256(prediction_out / 'receipt.json')
        summary['predictions_sha256'] = prediction_receipt['predictions_sha256']
        summary['query_sha256'] = prediction_receipt['query_sha256']
        with np.load(prediction_out / 'predictions.npz', allow_pickle=False) as z:
            actual_perts = [str(p) for p in z['perts']]
            actual_genes = [str(g) for g in z['genes']]
            actual_ids = [str(i) for i in z['members']]
            member_delta = z['member_delta'].copy()
            ensemble_delta = z['delta'].copy()
        if actual_perts != expected_perts or actual_genes != manifest['genes'] or actual_ids != [s[0] for s in SELECTIONS]:
            raise ValueError('reproduced condition/gene/member order changed')
        saved_members = []
        for index, member in enumerate(source_members):
            name = f"artifacts/{member['experiment_id']}/predictions.npz"
            path = Path(member['run_directory']) / name
            expected_hash = member['files_sha256'][name]
            if sha256(path) != expected_hash:
                raise ValueError('saved prediction source changed')
            with np.load(path, allow_pickle=False) as z:
                saved_perts = [str(p) for p in z['perts']]
                alphas = np.asarray(z['alphas'], dtype=float)
                matches = np.flatnonzero(alphas == member['selected_alpha'])
                if saved_perts != expected_perts or len(matches) != 1:
                    raise ValueError('saved prediction condition order/selected alpha mismatch')
                saved = z['delta'][int(matches[0])].copy()
            saved_members.append(saved)
            summary['member_comparisons'].append({
                'run_directory': member['run_directory'], 'experiment_id': member['experiment_id'],
                'alpha': member['selected_alpha'], 'full_grid_index': manifest['members'][index]['full_grid_index'],
                'saved_predictions_sha256': expected_hash, **comparison(member_delta[index], saved)})
        expected_ensemble = np.mean(np.stack(saved_members).astype(np.float64), axis=0).astype(np.float32)
        summary['ensemble_comparison'] = comparison(ensemble_delta, expected_ensemble)
        summary['n_conditions'] = len(expected_perts)
        summary['n_genes'] = len(manifest['genes'])
        if not all(c['passes_predeclared_tolerance'] for c in summary['member_comparisons']) or not summary['ensemble_comparison']['passes_predeclared_tolerance']:
            raise ValueError('saved prediction reproduction exceeded predeclared tolerance; no tolerance relaxation permitted')
        summary['status'] = 'passed'
    except BaseException as exc:
        summary['failure'] = {'type': type(exc).__name__, 'reason': str(exc)[:500]}
    finally:
        summary['finished_utc'] = utc()
        summary['elapsed_s'] = time.monotonic() - started
        summary['runtime'] = runtime_receipt()
        (out / 'RUNNING').unlink(missing_ok=True)
        summary['files_sha256'] = {
            str(p.relative_to(out)): sha256(p) for p in out.rglob('*') if p.is_file() and p.name != 'summary.json'}
        write_json(out / 'summary.json', summary)
    print(json.dumps({'status': summary['status'], 'summary': str(out / 'summary.json'),
                      'summary_sha256': sha256(out / 'summary.json')}, sort_keys=True))
    return 0 if summary['status'] == 'passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
