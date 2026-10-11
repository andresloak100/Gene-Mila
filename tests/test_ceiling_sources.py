"""The offline ceiling scripts read visible data only: their code (docstrings and comments aside) never
names the sealed labels, the private directory, the split file, or the oracle."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _code_without_docstrings(path: Path) -> str:
    tree = ast.parse(path.read_text())
    body = tree.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]
    return "\n".join(ast.unparse(node) for node in body)


def test_ceiling_scripts_never_name_sealed_data():
    for name in ("tools/ceiling_analysis.py", "tools/learned_kernel_experiment.py"):
        code = _code_without_docstrings(ROOT / name)
        for forbidden in ("private", "val2", "query_only", "splits.json", "QueryOracle", "LabelSet"):
            assert forbidden not in code, (name, forbidden)
