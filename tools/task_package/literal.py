"""Static caps on the data a foreign feature file may carry in its own source.

A feature plugin written outside the lab (by an autoresearch-style coding agent, Biomni, or a person translating
another system's ideas) is scored on out-of-fold predictions of the training perturbations. Such a file could paste
a table of training labels, or a few bits per perturbation, into literals and decode them at run time; the guard
(genemila/guard.py) stops file and network access but not that. These caps make it expensive, they do not make it
impossible: the deciding score for a foreign file is always one on perturbations whose labels its author never had
(visible validation or a fresh test), and tools/feature_compare.py says so in every report.

literal_check() is side-effect free and uses the standard library only, so both tools/feature_compare.py and the task
package's evaluate.py (which ships a byte-identical copy) import it.
"""
from __future__ import annotations

import ast

MAX_FILE_BYTES = 50_000
MAX_NUMERIC_CONSTANTS = 128      # every int/float/complex constant in the file, booleans excluded
MAX_DISPLAY_ELEMENTS = 24        # elements of one list/tuple/set/dict display
MAX_INT_ABS = 2 ** 31            # one huge integer can hold a whole table
MAX_FLOAT_REPR = 24              # characters of repr(float)
MAX_STRING_BYTES = 2_500         # all string and bytes constants together, docstrings and descriptions included
MAX_NAME_LITERALS = 40           # string constants equal to a perturbation or gene name of the bundle
DECODERS = {"frombuffer", "fromstring", "fromhex", "from_bytes", "to_bytes", "b64decode", "b32decode", "b16decode",
            "a85decode", "b85decode", "unhexlify", "literal_eval", "loads", "decompress"}


def literal_check(source: str, pair_ids=(), names=()) -> dict:
    """{"ok": bool, "problems": [...], "stats": {...}} for one plugin's source text.

    pair_ids: the ids of the bundle's perturbations of several genes (training and held-out ids are public); a string
    constant equal to one can only be a lookup key and is refused. names: the bundle's gene symbols and perturbation
    ids; string constants equal to one are counted and capped (a single gene's perturbation is named by its gene, so
    a marker-gene list and a per-perturbation table look alike, and only their size tells them apart)."""
    problems: list[str] = []
    size = len(source.encode())
    if size > MAX_FILE_BYTES:
        problems.append(f"file is {size} bytes (cap {MAX_FILE_BYTES})")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"ok": False, "problems": [f"syntax error: {exc}"], "stats": {"bytes": size}}
    multi = {str(p) for p in pair_ids}
    names = {str(n) for n in names} | multi
    n_num = n_str_bytes = n_name = 0
    pair_literals, decoders = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, bool) or v is None or v is Ellipsis:
                continue
            if isinstance(v, (int, float, complex)):
                n_num += 1
                if isinstance(v, int) and abs(v) >= MAX_INT_ABS:
                    problems.append(f"integer literal of {v.bit_length()} bits (cap {MAX_INT_ABS.bit_length() - 1})")
                if isinstance(v, float) and len(repr(v)) > MAX_FLOAT_REPR:
                    problems.append(f"float literal with {len(repr(v))} characters (cap {MAX_FLOAT_REPR})")
            elif isinstance(v, (str, bytes)):
                n_str_bytes += len(v.encode() if isinstance(v, str) else v)
                if isinstance(v, str):
                    if v in names:
                        n_name += 1
                    if v in multi:
                        pair_literals.add(v)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)) and len(node.elts) > MAX_DISPLAY_ELEMENTS:
            problems.append(f"literal display of {len(node.elts)} elements (cap {MAX_DISPLAY_ELEMENTS})")
        elif isinstance(node, ast.Dict) and len(node.keys) > MAX_DISPLAY_ELEMENTS:
            problems.append(f"dict display of {len(node.keys)} entries (cap {MAX_DISPLAY_ELEMENTS})")
        elif isinstance(node, ast.Attribute) and node.attr in DECODERS:
            decoders.add(node.attr)
        elif isinstance(node, ast.Name) and node.id in DECODERS:
            decoders.add(node.id)
    if n_num > MAX_NUMERIC_CONSTANTS:
        problems.append(f"{n_num} numeric constants (cap {MAX_NUMERIC_CONSTANTS})")
    if n_str_bytes > MAX_STRING_BYTES:
        problems.append(f"{n_str_bytes} bytes of string constants (cap {MAX_STRING_BYTES})")
    if n_name > MAX_NAME_LITERALS:
        problems.append(f"{n_name} string constants name a gene or perturbation (cap {MAX_NAME_LITERALS})")
    if pair_literals:
        problems.append(f"string constants name multi-gene perturbations: {sorted(pair_literals)[:3]}")
    if decoders:
        problems.append(f"decoding helpers not allowed: {sorted(decoders)}")
    stats = {"bytes": size, "numeric_constants": n_num, "string_bytes": n_str_bytes, "name_literals": n_name}
    return {"ok": not problems, "problems": sorted(set(problems)), "stats": stats}
