from genemila.research_state import KNOWLEDGE_SECTION_CHARS, SECTION_CHARS, TOTAL_CHARS, render_state

MARK = "\n- … (truncated)"


def _summary(n_chars):
    # lab.knowledge_summary() joins one entry per knowledge file with "; "
    line = "kw_file: dict of 10 entries, e.g. 'GENE': 'x'"
    return "; ".join(line for _ in range(n_chars // (len(line) + 2) + 1))[:n_chars]


def _section(text, title):
    return text.split(f"## {title}\n", 1)[1].split("\n## ", 1)[0]


def test_knowledge_section_gets_its_own_larger_budget():
    assert SECTION_CHARS == 2500 and KNOWLEDGE_SECTION_CHARS == 8000 and TOTAL_CHARS == 20000

    six_k = _summary(6000)
    text = render_state({"knowledge_available": six_k, "current_best": {"score": 0.5}})
    assert six_k in text and "truncated" not in text  # 6,000 characters are shown whole

    nine_k = _summary(9000)
    text = render_state({"knowledge_available": nine_k, "current_best": {"score": 0.5}})
    knowledge = _section(text, "KNOWLEDGE AVAILABLE")
    assert knowledge.endswith(MARK) and nine_k not in text
    assert KNOWLEDGE_SECTION_CHARS - 100 < len(knowledge) <= KNOWLEDGE_SECTION_CHARS + len(MARK)

    # every other section keeps the 2,500-character budget, and the whole render stays within TOTAL_CHARS
    other = [f"hypothesis {i} " + "x" * 80 for i in range(40)]  # about 3,000 characters rendered
    text = render_state({"knowledge_available": nine_k, "in_flight": other, "failed_directions": other,
                         "recent_experiments": other, "feature_registry": other, "current_best": {"score": 0.5}})
    inflight = _section(text, "IN FLIGHT")
    assert inflight.endswith(MARK) and len(inflight) <= SECTION_CHARS + len(MARK)
    assert "## CURRENT BEST" in text and len(text) <= TOTAL_CHARS
