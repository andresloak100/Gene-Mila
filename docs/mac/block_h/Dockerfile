# Block H (docs/PLAN_H_COMPARISON.md, Isolation, mode 1): the image the foreign agents run in. Built once, with
# network, from the operator's clone (the build context; nothing under data/ or runs/ is copied):
#   docker build -t genemila-h -f docs/mac/block_h/Dockerfile \
#     --build-arg PKG_REQS="$(tr '\n' ' ' < ~/gm_packages/adamson_cf_clean_tables/requirements.txt)" .
# At run time the container joins the internal network genemila_h (no route to the internet; its only way out is
# the relay to the ledger proxy on the Mac), mounts one package copy, one output directory and the proxy's log
# (read-only), and holds no key. Only tools/baselines/ is copied in: never genemila/, configs/ or any prompt of the lab
# (protocol, fairness controls 6 and 7); the runners import nothing from genemila, and the package's evaluate.py has its
# own harness/genemila.
FROM python:3.12-slim
ARG PKG_REQS="numpy scipy scikit-learn"
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git nodejs npm \
    && npm install -g @anthropic-ai/claude-code @openai/codex && rm -rf /var/lib/apt/lists/*
# Biomni 0.0.8 imports pandas, tqdm and langchain_openai on load (agent/a1.py, utils.py, model/retriever.py) and
# matplotlib for plots, without declaring them; langchain-openai's latest pulls a langchain-core 1.x that langgraph
# 0.3.18 refuses, so the langchain family is pinned to 0.3 (resolved together with `pip check` clean, 2026-11-01, after
# Astra's H image stopped on "No module named 'pandas'", #51 / PR #97). The last line fails the build, not the run.
RUN pip install --no-cache-dir $PKG_REQS biomni==0.0.8 langgraph==0.3.18 langchain==0.3.30 langchain-core==0.3.86 \
      langchain-openai==0.3.35 openai==2.54.0 pandas tqdm matplotlib python-dotenv requests \
    && pip check && python -c "from biomni.agent import A1; import langchain_openai, matplotlib.pyplot"
COPY tools/baselines /lab/tools/baselines
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
