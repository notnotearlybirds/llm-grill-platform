ARG ENGINE=vllm

FROM nvidia/cuda:13.0.0-devel-ubuntu24.04 AS base

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    jq python3-pip python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir \
        huggingface_hub==1.16.1 \
        llm-grill==0.1.4 \
        typer==0.25.0 \
        click==8.4.1

ENV PATH="/opt/venv/bin:/usr/local/cuda/bin:$PATH" \
    CUDA_HOME=/usr/local/cuda \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64

# ── vllm ─────────────────────────────────────────────────────────────────────
FROM base AS vllm

RUN /opt/venv/bin/pip install --no-cache-dir vllm==0.19.1

# ── llama.cpp ─────────────────────────────────────────────────────────────────
FROM base AS llamacpp

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    git cmake build-essential libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1

RUN git clone --depth 1 --branch master https://github.com/ggml-org/llama.cpp /opt/llama.cpp \
    && cmake -S /opt/llama.cpp -B /opt/llama.cpp/build \
        -DGGML_CUDA=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc \
        -DCMAKE_EXE_LINKER_FLAGS="-L/usr/local/cuda/lib64/stubs" \
        -DCMAKE_SHARED_LINKER_FLAGS="-L/usr/local/cuda/lib64/stubs" \
    && cmake --build /opt/llama.cpp/build --target llama-server -j$(nproc) \
    && ln -sf /opt/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server \
    && rm -rf /opt/llama.cpp/.git

# ── common entrypoint ─────────────────────────────────────────────────────────
FROM ${ENGINE:-vllm} AS final

COPY runner.sh /opt/runner/runner.sh
RUN chmod +x /opt/runner/runner.sh

ENTRYPOINT ["/opt/runner/runner.sh"]
