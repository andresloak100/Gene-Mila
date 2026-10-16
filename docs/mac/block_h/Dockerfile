# Block H (docs/PLAN_H_COMPARISON.md, Isolation, mode 1): the image the foreign agents run in. Built once, with
# network, from the operator's clone (the build context; nothing under data/ or runs/ is copied):
#   docker build -t genemila-h -f docs/mac/block_h/Dockerfile \
#     --build-arg PKG_REQS="$(tr '\n' ' ' < ~/gm_packages/adamson_cf_clean_tables/requirements.txt)" .
# At run time the container joins the internal network genemila_h (no route to the internet; its only way out is
# the relay to the ledger proxy on the Mac), mounts one package copy and one output directory, and holds no key.
FROM python:3.12-slim
ARG PKG_REQS="numpy scipy scikit-learn"
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git nodejs npm \
    && npm install -g @anthropic-ai/claude-code && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir $PKG_REQS biomni langchain langgraph==0.3.18 openai
COPY genemila /lab/genemila
COPY configs /lab/configs
COPY tools/baselines /lab/tools/baselines
ENV PYTHONPATH=/lab PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
