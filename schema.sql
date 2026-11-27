CREATE TABLE IF NOT EXISTS hardware (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    vendor TEXT NOT NULL,
    category TEXT NOT NULL,
    vram_gb REAL NOT NULL,
    bandwidth_gbs REAL NOT NULL,
    tdp_watts INTEGER,
    release_year INTEGER,
    msrp_usd INTEGER,
    amazon_query TEXT NOT NULL,
    cloud_gpu_equivalent TEXT
);

CREATE TABLE IF NOT EXISTS llm_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hf_repo_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    family TEXT NOT NULL,
    total_params_b REAL NOT NULL,
    active_params_b REAL NOT NULL,
    is_moe INTEGER DEFAULT 0,
    hidden_layers INTEGER NOT NULL,
    kv_heads INTEGER NOT NULL,
    head_dim INTEGER NOT NULL,
    max_context INTEGER NOT NULL,
    ollama_tag TEXT NOT NULL,
    license TEXT DEFAULT 'Apache-2.0'
);

CREATE TABLE IF NOT EXISTS compatibility_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    hardware_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    vram_q4_km_gb REAL NOT NULL,
    vram_q5_km_gb REAL NOT NULL,
    vram_q8_0_gb REAL NOT NULL,
    vram_fp16_gb REAL NOT NULL,
    kv_cache_8k_gb REAL NOT NULL,
    kv_cache_32k_gb REAL NOT NULL,
    total_req_8k_q4_gb REAL NOT NULL,
    verdict_code TEXT NOT NULL,
    verdict_label TEXT NOT NULL,
    est_tokens_per_sec REAL NOT NULL,
    recommended_quant TEXT NOT NULL,
    gpu_layers_offload TEXT NOT NULL,
    cli_ollama_cmd TEXT NOT NULL,
    cli_llamacpp_cmd TEXT NOT NULL,
    monetization_route TEXT NOT NULL,
    direct_answer_capsule TEXT NOT NULL,
    status TEXT DEFAULT 'enriched',
    published_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (hardware_id) REFERENCES hardware(id),
    FOREIGN KEY (model_id) REFERENCES llm_models(id)
);

CREATE INDEX IF NOT EXISTS idx_matrix_status ON compatibility_matrix(status);
CREATE INDEX IF NOT EXISTS idx_matrix_hw ON compatibility_matrix(hardware_id);
CREATE INDEX IF NOT EXISTS idx_matrix_model ON compatibility_matrix(model_id);
