"""Two text-only reviews through the existing gateway; no model/search/evaluation calls.
Run with DEEPSEEK_API_KEY supplied by the invoking shell; never print exceptions.
Inputs are a fixed JSON config and two public-metadata prompts published before calls.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from genemila.db import Database
from genemila.llm import LLMGateway, SpendLedger
from genemila.providers.base import ProviderError
from genemila.providers.openai_compat import DeepSeekProvider


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SafeDeepSeek(DeepSeekProvider):
    def complete(self, *args, **kwargs):
        try:
            response = super().complete(*args, **kwargs)
            key = os.environ.get('DEEPSEEK_API_KEY', '')
            self.credential_echo = any(key and key in str(getattr(response, field))
                                       for field in ('text', 'model', 'finish_reason'))
            if self.credential_echo:
                # Sanitize BEFORE gateway persistence, but retain usage for accounting.
                response.text = '[discarded: credential echo]'
                response.model = self.model
                response.finish_reason = 'credential_echo'
            del key
            return response
        except BaseException as exc:
            # Provider messages may echo arbitrary server content. Never log them.
            raise ProviderError(type(exc).__name__, retryable=False) from None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    config_path = args.config.resolve()
    cfg = json.loads(config_path.read_text())
    assert cfg['max_calls'] == 2 and len(cfg['reviews']) == 2
    assert cfg['budget']['max_total_usd'] == .25
    assert cfg['budget']['max_planner_usd'] == .001  # unused; avoids gateway's zero-cap auto-scaling
    assert cfg['budget']['cumulative_usd']['deepseek'] == 48
    assert cfg['budget']['api_retries'] == 0
    assert cfg['model'] == 'deepseek-v4-pro'
    out = args.out.resolve()
    assert out.is_relative_to(ROOT / 'runs') and not out.exists()
    ledger_path = Path(cfg['budget']['ledger'])
    assert ledger_path.is_file(), 'Refuse a missing/shared-ledger replacement'
    # A read-only preflight must not initialize or migrate the ledger.
    import sqlite3
    with sqlite3.connect(f'file:{ledger_path}?mode=ro', uri=True) as conn:
        ledger_before = conn.execute("SELECT COALESCE(SUM(cost_usd),0) FROM spend WHERE provider='deepseek'").fetchone()[0]
    assert ledger_before + .251 <= 48
    p = cfg['pricing'][cfg['model']]
    prompts = []
    worst = 0
    for review in cfg['reviews']:
        source = config_path.parent / review['prompt']
        assert sha(source) == review['sha256']
        user = source.read_text()
        # UTF-8 bytes plus overhead deliberately overestimates text input tokens.
        est = len((cfg['system'] + user).encode()) + 1024
        cost = (est * p['input_cache_miss'] + cfg['max_output_tokens'] * p['output']) / 1e6
        worst += cost
        prompts.append((review, user, est))
    assert worst <= .25
    preflight = {'status': 'preflight_passed', 'ledger_before': ledger_before,
                 'worst_case_total_usd': worst, 'max_calls': 2,
                 'config_sha256': sha(config_path), 'driver_sha256': sha(Path(__file__))}
    if args.preflight_only:
        print(json.dumps(preflight, sort_keys=True))
        return
    assert os.environ.get('DEEPSEEK_API_KEY'), 'Credential unavailable'
    out.mkdir()
    (out/'config.json').write_bytes(config_path.read_bytes())
    started = time.time()
    summary = {**preflight, 'status': 'started', 'started_at_unix': started,
               'reviews': [], 'new_model_scores': False, 'responses_or_labels_read': False}
    def deadline(signum, frame):
        raise TimeoutError('review deadline')
    old_handler = signal.signal(signal.SIGALRM, deadline)
    signal.alarm(300)
    try:
        ledger = SpendLedger(ledger_path)
        db = Database(out/'review.sqlite')
        gateway = LLMGateway(db, cfg, out.name, ledger=ledger)
        for review, user, est in prompts:
            if time.time() - started > 175:
                raise TimeoutError('insufficient deadline remaining for next request')
            provider = SafeDeepSeek(model=cfg['model'], timeout_s=120, thinking='disabled')
            response = gateway.call(provider, 'complete', role='worker', max_tokens=cfg['max_output_tokens'],
                                    est_input_tokens=est, worker_id=review['id'],
                                    system=cfg['system'], user=user)
            if provider.credential_echo:
                raise RuntimeError('credential echo detected; response discarded after accounting')
            response_path = out / (review['id'] + '.md')
            response_path.write_text(response.text)
            summary['reviews'].append({'id': review['id'], 'served_model': response.model,
                'finish_reason': response.finish_reason, 'usage': vars(response.usage),
                'response_sha256': sha(response_path)})
            if response.model not in {cfg['model'], 'deepseek-v4-pro-0813'}:
                raise RuntimeError('unexpected served model; no follow-up or retry')
            if response.finish_reason != 'stop' or not response.text.strip():
                raise RuntimeError('incomplete response; no follow-up or retry')
        summary['status'] = 'completed'
    except BaseException as exc:
        summary['status'] = 'stopped'
        summary['error_type'] = type(exc).__name__
        summary['billing_caveat'] = 'Failed/interrupted requests may have unreported provider usage; no retry.'
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        with sqlite3.connect(f'file:{ledger_path}?mode=ro', uri=True) as conn:
            ledger_after = conn.execute("SELECT COALESCE(SUM(cost_usd),0) FROM spend WHERE provider='deepseek'").fetchone()[0]
        summary.update(finished_at_unix=time.time(), ledger_after=ledger_after,
                       ledger_increment_usd=ledger_after-ledger_before)
        (out/'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:summary[k] for k in ('status','ledger_before','ledger_after','ledger_increment_usd')}))
    if summary['status'] != 'completed':
        raise SystemExit(2)

if __name__ == '__main__':
    main()
