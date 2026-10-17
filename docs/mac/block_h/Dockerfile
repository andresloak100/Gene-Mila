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
RUN pip install --no-cache-dir $PKG_REQS biomni langchain langgraph==0.3.18 openai
COPY tools/baselines /lab/tools/baselines
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
