import json
import math
import sqlite3
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

DB_FILE = "llm_staging.db"
SCHEMA_FILE = "schema.sql"

# Katalog 32 GPU Konsumen, Workstation, dan Apple Silicon Unified Memory
HARDWARE_CATALOG: List[Dict[str, Any]] = [
    # NVIDIA RTX 50-Series
    {"name": "NVIDIA RTX 5090 32GB", "slug": "rtx-5090-32gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 32.0, "bandwidth_gbs": 1792.0, "tdp_watts": 575, "release_year": 2025, "msrp_usd": 1999, "amazon_query": "NVIDIA RTX 5090 32GB Graphics Card", "cloud_gpu": "RTX 5090 / A100 40GB"},
    {"name": "NVIDIA RTX 5080 16GB", "slug": "rtx-5080-16gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 960.0, "tdp_watts": 360, "release_year": 2025, "msrp_usd": 999, "amazon_query": "NVIDIA RTX 5080 16GB Graphics Card", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "NVIDIA RTX 5070 Ti 16GB", "slug": "rtx-5070-ti-16gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 896.0, "tdp_watts": 300, "release_year": 2025, "msrp_usd": 749, "amazon_query": "NVIDIA RTX 5070 Ti 16GB Graphics Card", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "NVIDIA RTX 5070 12GB", "slug": "rtx-5070-12gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 12.0, "bandwidth_gbs": 672.0, "tdp_watts": 250, "release_year": 2025, "msrp_usd": 549, "amazon_query": "NVIDIA RTX 5070 12GB Graphics Card", "cloud_gpu": "RTX A5000 24GB"},
    {"name": "NVIDIA RTX 5060 Ti 16GB", "slug": "rtx-5060-ti-16gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 448.0, "tdp_watts": 180, "release_year": 2025, "msrp_usd": 429, "amazon_query": "NVIDIA RTX 5060 Ti 16GB Graphics Card", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "NVIDIA RTX 5060 8GB", "slug": "rtx-5060-8gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 8.0, "bandwidth_gbs": 448.0, "tdp_watts": 145, "release_year": 2025, "msrp_usd": 299, "amazon_query": "NVIDIA RTX 5060 8GB Graphics Card", "cloud_gpu": "RTX 3090 24GB"},
    # NVIDIA RTX 40-Series
    {"name": "NVIDIA RTX 4090 24GB", "slug": "rtx-4090-24gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 24.0, "bandwidth_gbs": 1008.0, "tdp_watts": 450, "release_year": 2022, "msrp_usd": 1599, "amazon_query": "NVIDIA RTX 4090 24GB Graphics Card", "cloud_gpu": "A100 80GB"},
    {"name": "NVIDIA RTX 4080 Super 16GB", "slug": "rtx-4080-super-16gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 736.0, "tdp_watts": 320, "release_year": 2024, "msrp_usd": 999, "amazon_query": "NVIDIA RTX 4080 Super 16GB Graphics Card", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "NVIDIA RTX 4070 Ti Super 16GB", "slug": "rtx-4070-ti-super-16gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 672.0, "tdp_watts": 285, "release_year": 2024, "msrp_usd": 799, "amazon_query": "NVIDIA RTX 4070 Ti Super 16GB", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "NVIDIA RTX 4070 Super 12GB", "slug": "rtx-4070-super-12gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 12.0, "bandwidth_gbs": 504.0, "tdp_watts": 220, "release_year": 2024, "msrp_usd": 599, "amazon_query": "NVIDIA RTX 4070 Super 12GB", "cloud_gpu": "RTX A5000 24GB"},
    {"name": "NVIDIA RTX 4060 Ti 16GB", "slug": "rtx-4060-ti-16gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 288.0, "tdp_watts": 165, "release_year": 2023, "msrp_usd": 499, "amazon_query": "NVIDIA RTX 4060 Ti 16GB Graphics Card", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "NVIDIA RTX 4060 8GB", "slug": "rtx-4060-8gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 8.0, "bandwidth_gbs": 272.0, "tdp_watts": 115, "release_year": 2023, "msrp_usd": 299, "amazon_query": "NVIDIA RTX 4060 8GB Graphics Card", "cloud_gpu": "RTX 3090 24GB"},
    {"name": "NVIDIA RTX 4060 Laptop 8GB", "slug": "rtx-4060-laptop-8gb", "vendor": "NVIDIA", "category": "Laptop GPU", "vram_gb": 8.0, "bandwidth_gbs": 256.0, "tdp_watts": 115, "release_year": 2023, "msrp_usd": 1099, "amazon_query": "RTX 4060 Gaming Laptop 32GB RAM", "cloud_gpu": "RTX 3090 24GB"},
    # NVIDIA RTX 30-Series & Workstation
    {"name": "NVIDIA RTX 3090 24GB", "slug": "rtx-3090-24gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 24.0, "bandwidth_gbs": 936.0, "tdp_watts": 350, "release_year": 2020, "msrp_usd": 1499, "amazon_query": "NVIDIA RTX 3090 24GB Graphics Card", "cloud_gpu": "A100 80GB"},
    {"name": "NVIDIA RTX 3080 10GB", "slug": "rtx-3080-10gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 10.0, "bandwidth_gbs": 760.0, "tdp_watts": 320, "release_year": 2020, "msrp_usd": 699, "amazon_query": "NVIDIA RTX 4070 Super 12GB Upgrade", "cloud_gpu": "RTX 3090 24GB"},
    {"name": "NVIDIA RTX 3060 12GB", "slug": "rtx-3060-12gb", "vendor": "NVIDIA", "category": "Desktop GPU", "vram_gb": 12.0, "bandwidth_gbs": 360.0, "tdp_watts": 170, "release_year": 2021, "msrp_usd": 329, "amazon_query": "NVIDIA RTX 3060 12GB Graphics Card", "cloud_gpu": "RTX 3090 24GB"},
    {"name": "NVIDIA RTX 3060 Laptop 6GB", "slug": "rtx-3060-laptop-6gb", "vendor": "NVIDIA", "category": "Laptop GPU", "vram_gb": 6.0, "bandwidth_gbs": 336.0, "tdp_watts": 115, "release_year": 2021, "msrp_usd": 899, "amazon_query": "RTX 4070 Laptop 16GB VRAM", "cloud_gpu": "RTX 3090 24GB"},
    {"name": "NVIDIA RTX A6000 48GB", "slug": "rtx-a6000-48gb", "vendor": "NVIDIA", "category": "Workstation GPU", "vram_gb": 48.0, "bandwidth_gbs": 768.0, "tdp_watts": 300, "release_year": 2020, "msrp_usd": 4650, "amazon_query": "NVIDIA RTX A6000 48GB Workstation", "cloud_gpu": "A100 80GB"},
    # AMD Radeon
    {"name": "AMD Radeon RX 7900 XTX 24GB", "slug": "rx-7900-xtx-24gb", "vendor": "AMD", "category": "Desktop GPU", "vram_gb": 24.0, "bandwidth_gbs": 960.0, "tdp_watts": 355, "release_year": 2022, "msrp_usd": 999, "amazon_query": "AMD Radeon RX 7900 XTX 24GB", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "AMD Radeon RX 7900 XT 20GB", "slug": "rx-7900-xt-20gb", "vendor": "AMD", "category": "Desktop GPU", "vram_gb": 20.0, "bandwidth_gbs": 800.0, "tdp_watts": 315, "release_year": 2022, "msrp_usd": 899, "amazon_query": "AMD Radeon RX 7900 XT 20GB", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "AMD Radeon RX 9070 XT 16GB", "slug": "rx-9070-xt-16gb", "vendor": "AMD", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 640.0, "tdp_watts": 304, "release_year": 2025, "msrp_usd": 599, "amazon_query": "AMD Radeon RX 9070 XT 16GB", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "AMD Radeon RX 7800 XT 16GB", "slug": "rx-7800-xt-16gb", "vendor": "AMD", "category": "Desktop GPU", "vram_gb": 16.0, "bandwidth_gbs": 624.0, "tdp_watts": 263, "release_year": 2023, "msrp_usd": 499, "amazon_query": "AMD Radeon RX 7800 XT 16GB", "cloud_gpu": "RTX 4090 24GB"},
    # Apple Silicon Unified Memory (Alokasi GPU efektif ~75% dari total RAM sistem)
    {"name": "Apple M4 Max 128GB", "slug": "apple-m4-max-128gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 96.0, "bandwidth_gbs": 546.0, "tdp_watts": 90, "release_year": 2024, "msrp_usd": 4699, "amazon_query": "Apple MacBook Pro M4 Max", "cloud_gpu": "H100 80GB"},
    {"name": "Apple M4 Max 64GB", "slug": "apple-m4-max-64gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 48.0, "bandwidth_gbs": 546.0, "tdp_watts": 90, "release_year": 2024, "msrp_usd": 3699, "amazon_query": "Apple MacBook Pro M4 Max", "cloud_gpu": "A100 80GB"},
    {"name": "Apple M4 Pro 48GB", "slug": "apple-m4-pro-48gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 36.0, "bandwidth_gbs": 273.0, "tdp_watts": 65, "release_year": 2024, "msrp_usd": 2399, "amazon_query": "Apple Mac Mini M4 Pro 48GB", "cloud_gpu": "A100 40GB"},
    {"name": "Apple M4 Pro 24GB", "slug": "apple-m4-pro-24gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 18.0, "bandwidth_gbs": 273.0, "tdp_watts": 65, "release_year": 2024, "msrp_usd": 1399, "amazon_query": "Apple Mac Mini M4 Pro 24GB", "cloud_gpu": "RTX 4090 24GB"},
    {"name": "Apple M4 16GB", "slug": "apple-m4-16gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 11.5, "bandwidth_gbs": 120.0, "tdp_watts": 35, "release_year": 2024, "msrp_usd": 599, "amazon_query": "Apple Mac Mini M4 16GB", "cloud_gpu": "RTX 3090 24GB"},
    {"name": "Apple M3 Max 96GB", "slug": "apple-m3-max-96gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 72.0, "bandwidth_gbs": 400.0, "tdp_watts": 85, "release_year": 2023, "msrp_usd": 3999, "amazon_query": "Apple MacBook Pro M3 Max", "cloud_gpu": "A100 80GB"},
    {"name": "Apple M2 Ultra 192GB", "slug": "apple-m2-ultra-192gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 144.0, "bandwidth_gbs": 800.0, "tdp_watts": 150, "release_year": 2023, "msrp_usd": 4999, "amazon_query": "Apple Mac Studio M2 Ultra", "cloud_gpu": "H100 80GB"},
    {"name": "Apple M2 Max 32GB", "slug": "apple-m2-max-32gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 24.0, "bandwidth_gbs": 400.0, "tdp_watts": 75, "release_year": 2023, "msrp_usd": 2499, "amazon_query": "Apple Mac Studio M2 Max", "cloud_gpu": "A100 40GB"},
    {"name": "Apple M1 Max 32GB", "slug": "apple-m1-max-32gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 24.0, "bandwidth_gbs": 400.0, "tdp_watts": 70, "release_year": 2021, "msrp_usd": 1999, "amazon_query": "Apple MacBook Pro M1 Max 32GB", "cloud_gpu": "A100 40GB"},
    {"name": "Apple M1 16GB", "slug": "apple-m1-16gb", "vendor": "Apple", "category": "Apple Silicon", "vram_gb": 11.5, "bandwidth_gbs": 68.25, "tdp_watts": 30, "release_year": 2020, "msrp_usd": 799, "amazon_query": "Apple Mac Mini M4 Pro", "cloud_gpu": "RTX 3090 24GB"},
]

# Katalog 30 Model Open-Weight Terpopuler + Fallback Arsitektur Akurat
MODEL_CATALOG: List[Dict[str, Any]] = [
    # DeepSeek R1 Distill Series
    {"hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", "name": "DeepSeek R1 Distill Qwen 1.5B", "slug": "deepseek-r1-distill-qwen-1-5b", "family": "DeepSeek R1", "total_b": 1.78, "active_b": 1.78, "is_moe": 0, "layers": 28, "kv_heads": 2, "head_dim": 128, "max_ctx": 131072, "ollama": "deepseek-r1:1.5b"},
    {"hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "name": "DeepSeek R1 Distill Qwen 7B", "slug": "deepseek-r1-distill-qwen-7b", "family": "DeepSeek R1", "total_b": 7.62, "active_b": 7.62, "is_moe": 0, "layers": 28, "kv_heads": 4, "head_dim": 128, "max_ctx": 131072, "ollama": "deepseek-r1:7b"},
    {"hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", "name": "DeepSeek R1 Distill Llama 8B", "slug": "deepseek-r1-distill-llama-8b", "family": "DeepSeek R1", "total_b": 8.03, "active_b": 8.03, "is_moe": 0, "layers": 32, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "deepseek-r1:8b"},
    {"hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B", "name": "DeepSeek R1 Distill Qwen 14B", "slug": "deepseek-r1-distill-qwen-14b", "family": "DeepSeek R1", "total_b": 14.77, "active_b": 14.77, "is_moe": 0, "layers": 48, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "deepseek-r1:14b"},
    {"hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "name": "DeepSeek R1 Distill Qwen 32B", "slug": "deepseek-r1-distill-qwen-32b", "family": "DeepSeek R1", "total_b": 32.76, "active_b": 32.76, "is_moe": 0, "layers": 64, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "deepseek-r1:32b"},
    {"hf_repo": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B", "name": "DeepSeek R1 Distill Llama 70B", "slug": "deepseek-r1-distill-llama-70b", "family": "DeepSeek R1", "total_b": 70.55, "active_b": 70.55, "is_moe": 0, "layers": 80, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "deepseek-r1:70b"},
    # Qwen 3 & Qwen 2.5 Series
    {"hf_repo": "Qwen/Qwen3-4B", "name": "Qwen 3 4B", "slug": "qwen-3-4b", "family": "Qwen 3", "total_b": 4.02, "active_b": 4.02, "is_moe": 0, "layers": 36, "kv_heads": 8, "head_dim": 128, "max_ctx": 40960, "ollama": "qwen3:4b"},
    {"hf_repo": "Qwen/Qwen3-8B", "name": "Qwen 3 8B", "slug": "qwen-3-8b", "family": "Qwen 3", "total_b": 8.19, "active_b": 8.19, "is_moe": 0, "layers": 36, "kv_heads": 8, "head_dim": 128, "max_ctx": 40960, "ollama": "qwen3:8b"},
    {"hf_repo": "Qwen/Qwen3-14B", "name": "Qwen 3 14B", "slug": "qwen-3-14b", "family": "Qwen 3", "total_b": 14.80, "active_b": 14.80, "is_moe": 0, "layers": 40, "kv_heads": 8, "head_dim": 128, "max_ctx": 40960, "ollama": "qwen3:14b"},
    {"hf_repo": "Qwen/Qwen3-30B-A3B", "name": "Qwen 3 30B-A3B (MoE)", "slug": "qwen-3-30b-a3b-moe", "family": "Qwen 3", "total_b": 30.53, "active_b": 3.30, "is_moe": 1, "layers": 48, "kv_heads": 4, "head_dim": 128, "max_ctx": 40960, "ollama": "qwen3:30b-a3b"},
    {"hf_repo": "Qwen/Qwen3-32B", "name": "Qwen 3 32B", "slug": "qwen-3-32b", "family": "Qwen 3", "total_b": 32.76, "active_b": 32.76, "is_moe": 0, "layers": 64, "kv_heads": 8, "head_dim": 128, "max_ctx": 40960, "ollama": "qwen3:32b"},
    {"hf_repo": "Qwen/Qwen2.5-Coder-7B-Instruct", "name": "Qwen 2.5 Coder 7B", "slug": "qwen-2-5-coder-7b", "family": "Qwen 2.5 Coder", "total_b": 7.62, "active_b": 7.62, "is_moe": 0, "layers": 28, "kv_heads": 4, "head_dim": 128, "max_ctx": 32768, "ollama": "qwen2.5-coder:7b"},
    {"hf_repo": "Qwen/Qwen2.5-Coder-14B-Instruct", "name": "Qwen 2.5 Coder 14B", "slug": "qwen-2-5-coder-14b", "family": "Qwen 2.5 Coder", "total_b": 14.77, "active_b": 14.77, "is_moe": 0, "layers": 48, "kv_heads": 8, "head_dim": 128, "max_ctx": 32768, "ollama": "qwen2.5-coder:14b"},
    {"hf_repo": "Qwen/Qwen2.5-Coder-32B-Instruct", "name": "Qwen 2.5 Coder 32B", "slug": "qwen-2-5-coder-32b", "family": "Qwen 2.5 Coder", "total_b": 32.76, "active_b": 32.76, "is_moe": 0, "layers": 64, "kv_heads": 8, "head_dim": 128, "max_ctx": 32768, "ollama": "qwen2.5-coder:32b"},
    {"hf_repo": "Qwen/Qwen2.5-72B-Instruct", "name": "Qwen 2.5 72B", "slug": "qwen-2-5-72b", "family": "Qwen 2.5", "total_b": 72.71, "active_b": 72.71, "is_moe": 0, "layers": 80, "kv_heads": 8, "head_dim": 128, "max_ctx": 32768, "ollama": "qwen2.5:72b"},
    # Meta Llama Series
    {"hf_repo": "meta-llama/Llama-3.2-3B-Instruct", "name": "Llama 3.2 3B", "slug": "llama-3-2-3b", "family": "Llama 3", "total_b": 3.21, "active_b": 3.21, "is_moe": 0, "layers": 28, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "llama3.2:3b"},
    {"hf_repo": "meta-llama/Llama-3.1-8B-Instruct", "name": "Llama 3.1 8B", "slug": "llama-3-1-8b", "family": "Llama 3", "total_b": 8.03, "active_b": 8.03, "is_moe": 0, "layers": 32, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "llama3.1:8b"},
    {"hf_repo": "meta-llama/Llama-3.3-70B-Instruct", "name": "Llama 3.3 70B", "slug": "llama-3-3-70b", "family": "Llama 3", "total_b": 70.55, "active_b": 70.55, "is_moe": 0, "layers": 80, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "llama3.3:70b"},
    {"hf_repo": "meta-llama/Llama-4-Scout-17B-16E-Instruct", "name": "Llama 4 Scout 109B (17B Active MoE)", "slug": "llama-4-scout-17b-16e", "family": "Llama 4", "total_b": 109.0, "active_b": 17.0, "is_moe": 1, "layers": 48, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "llama4:scout"},
    # Google Gemma 3 & Gemma 2 Series
    {"hf_repo": "google/gemma-3-4b-it", "name": "Gemma 3 4B", "slug": "gemma-3-4b", "family": "Gemma 3", "total_b": 4.30, "active_b": 4.30, "is_moe": 0, "layers": 34, "kv_heads": 4, "head_dim": 256, "max_ctx": 131072, "ollama": "gemma3:4b"},
    {"hf_repo": "google/gemma-3-12b-it", "name": "Gemma 3 12B", "slug": "gemma-3-12b", "family": "Gemma 3", "total_b": 12.19, "active_b": 12.19, "is_moe": 0, "layers": 48, "kv_heads": 8, "head_dim": 256, "max_ctx": 131072, "ollama": "gemma3:12b"},
    {"hf_repo": "google/gemma-3-27b-it", "name": "Gemma 3 27B", "slug": "gemma-3-27b", "family": "Gemma 3", "total_b": 27.43, "active_b": 27.43, "is_moe": 0, "layers": 62, "kv_heads": 16, "head_dim": 128, "max_ctx": 131072, "ollama": "gemma3:27b"},
    {"hf_repo": "google/gemma-2-9b-it", "name": "Gemma 2 9B", "slug": "gemma-2-9b", "family": "Gemma 2", "total_b": 9.24, "active_b": 9.24, "is_moe": 0, "layers": 42, "kv_heads": 8, "head_dim": 256, "max_ctx": 8192, "ollama": "gemma2:9b"},
    {"hf_repo": "google/gemma-2-27b-it", "name": "Gemma 2 27B", "slug": "gemma-2-27b", "family": "Gemma 2", "total_b": 27.23, "active_b": 27.23, "is_moe": 0, "layers": 46, "kv_heads": 16, "head_dim": 128, "max_ctx": 8192, "ollama": "gemma2:27b"},
    # Microsoft Phi & Mistral Series
    {"hf_repo": "microsoft/phi-4", "name": "Microsoft Phi-4 14B", "slug": "phi-4-14b", "family": "Phi-4", "total_b": 14.66, "active_b": 14.66, "is_moe": 0, "layers": 40, "kv_heads": 10, "head_dim": 128, "max_ctx": 16384, "ollama": "phi4:14b"},
    {"hf_repo": "microsoft/Phi-4-reasoning-plus", "name": "Microsoft Phi-4 Reasoning Plus 14B", "slug": "phi-4-reasoning-plus-14b", "family": "Phi-4", "total_b": 14.66, "active_b": 14.66, "is_moe": 0, "layers": 40, "kv_heads": 10, "head_dim": 128, "max_ctx": 32768, "ollama": "phi4-reasoning:plus"},
    {"hf_repo": "mistralai/Mistral-7B-Instruct-v0.3", "name": "Mistral 7B v0.3", "slug": "mistral-7b-v0-3", "family": "Mistral", "total_b": 7.25, "active_b": 7.25, "is_moe": 0, "layers": 32, "kv_heads": 8, "head_dim": 128, "max_ctx": 32768, "ollama": "mistral:7b"},
    {"hf_repo": "mistralai/Mistral-Small-24B-Instruct-2501", "name": "Mistral Small 3 24B", "slug": "mistral-small-3-24b", "family": "Mistral", "total_b": 23.57, "active_b": 23.57, "is_moe": 0, "layers": 40, "kv_heads": 8, "head_dim": 128, "max_ctx": 32768, "ollama": "mistral-small:24b"},
    {"hf_repo": "mistralai/Devstral-Small-2505", "name": "Mistral Devstral Small 24B", "slug": "devstral-small-24b", "family": "Mistral", "total_b": 23.57, "active_b": 23.57, "is_moe": 0, "layers": 40, "kv_heads": 8, "head_dim": 128, "max_ctx": 131072, "ollama": "devstral:24b"},
    {"hf_repo": "mistralai/Mixtral-8x7B-Instruct-v0.1", "name": "Mixtral 8x7B (MoE)", "slug": "mixtral-8x7b-moe", "family": "Mixtral", "total_b": 46.70, "active_b": 12.90, "is_moe": 1, "layers": 32, "kv_heads": 8, "head_dim": 128, "max_ctx": 32768, "ollama": "mixtral:8x7b"},
]


def fetch_hf_config(repo_id: str) -> Dict[str, Any]:
    url = f"https://huggingface.co/{repo_id}/resolve/main/config.json"
    req = urllib.request.Request(url, headers={"User-Agent": "GoDedi-LLM-Spec-Miner/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}


def calculate_matrix_row(hw: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    total_b = mod["total_b"]
    active_b = mod["active_b"]

    # Bobot model dalam GB berdasarkan bit-per-weight efektif GGUF standar
    vram_q4_km = round(total_b * 0.61, 2)
    vram_q5_km = round(total_b * 0.73, 2)
    vram_q8_0 = round(total_b * 1.07, 2)
    vram_fp16 = round(total_b * 2.00, 2)

    # KV-Cache FP16 (2 * layers * kv_heads * head_dim * 2 bytes) per token
    kv_bytes_per_token = 2 * mod["layers"] * mod["kv_heads"] * mod["head_dim"] * 2
    kv_cache_8k = round((kv_bytes_per_token * 8192) / (1024 ** 3), 2)
    kv_cache_32k = round((kv_bytes_per_token * 32768) / (1024 ** 3), 2)

    os_overhead = 0.85
    total_req_8k_q4 = round(vram_q4_km + kv_cache_8k + os_overhead, 2)
    total_req_8k_q8 = round(vram_q8_0 + kv_cache_8k + os_overhead, 2)

    avail_vram = hw["vram_gb"]
    bw = hw["bandwidth_gbs"]

    # Kecepatan teoritis full GPU offload (memory-bandwidth bound, efisiensi nyata ~68%)
    active_q4_gb = max(active_b * 0.61, 0.5)
    full_gpu_tps = round((bw / active_q4_gb) * 0.68, 1)

    if avail_vram >= total_req_8k_q8:
        verdict_code = "OPTIMAL_Q8"
        verdict_label = "Runs Smoothly at Q8_0 (Near-Lossless)"
        rec_quant = "Q8_0 (8-bit)"
        layers_str = f"All {mod['layers']}/{mod['layers']} layers (100% GPU)"
        est_tps = round(full_gpu_tps * 0.62, 1)
        route = "LOCAL_HARDWARE_CTA"
        capsule = (
            f"Yes — the {hw['name']} ({avail_vram:.0f} GB VRAM) easily runs {mod['name']} at Q8_0 precision "
            f"({total_req_8k_q8:.1f} GB total with 8K context), delivering ~{est_tps} tokens/sec with zero CPU offload."
        )
    elif avail_vram >= total_req_8k_q4:
        verdict_code = "OPTIMAL_Q4"
        verdict_label = "Runs Smoothly at Q4_K_M (Full GPU)"
        rec_quant = "Q4_K_M (4-bit)"
        layers_str = f"All {mod['layers']}/{mod['layers']} layers (100% GPU)"
        est_tps = full_gpu_tps
        route = "LOCAL_HARDWARE_CTA"
        capsule = (
            f"Yes — the {hw['name']} ({avail_vram:.0f} GB VRAM) fits {mod['name']} Q4_K_M completely in VRAM "
            f"({total_req_8k_q4:.1f} GB needed at 8K context), achieving ~{est_tps} tokens/sec."
        )
    elif avail_vram >= (vram_q4_km + 0.5 + os_overhead):
        verdict_code = "TIGHT_FIT_4K"
        verdict_label = "Fits at Q4_K_M (Cap Context to 4K)"
        rec_quant = "Q4_K_M (4K Context)"
        layers_str = f"All {mod['layers']}/{mod['layers']} layers (4K ctx limit)"
        est_tps = round(full_gpu_tps * 0.90, 1)
        route = "LOCAL_HARDWARE_CTA"
        capsule = (
            f"Yes, with a tight fit — {mod['name']} Q4_K_M requires {total_req_8k_q4:.1f} GB at 8K context, "
            f"so capping context to 4,096 tokens lets your {hw['name']} run it at ~{est_tps} tokens/sec."
        )
    elif avail_vram >= (vram_q4_km * 0.45):
        ratio = max(0.25, min(0.85, (avail_vram - os_overhead) / max(vram_q4_km, 1.0)))
        offload_layers = max(1, int(math.floor(mod["layers"] * ratio)))
        verdict_code = "PARTIAL_OFFLOAD"
        verdict_label = "Partial GPU+RAM Offload (Slower)"
        rec_quant = "Q4_K_M (Split CPU/GPU)"
        layers_str = f"{offload_layers}/{mod['layers']} layers on GPU + System RAM"
        est_tps = round(max(1.8, full_gpu_tps * ratio * 0.22), 1)
        route = "CLOUD_GPU_CTA"
        capsule = (
            f"Partially — {mod['name']} Q4_K_M needs {total_req_8k_q4:.1f} GB VRAM, exceeding the {hw['name']}'s "
            f"{avail_vram:.0f} GB. Offloading {offload_layers}/{mod['layers']} layers to system RAM yields ~{est_tps} tokens/sec."
        )
    else:
        verdict_code = "OOM_CLOUD"
        verdict_label = "Out of Memory (Cloud GPU Recommended)"
        rec_quant = "Cloud GPU Required"
        layers_str = "0 layers (Exceeds VRAM capacity)"
        est_tps = 0.0
        route = "CLOUD_GPU_CTA"
        capsule = (
            f"No — {mod['name']} requires {total_req_8k_q4:.1f} GB VRAM at Q4_K_M, which causes an Out-of-Memory (OOM) "
            f"error on the {hw['name']} ({avail_vram:.0f} GB). Renting a cloud {hw['cloud_gpu']} is recommended."
        )

    ngl_flag = "99" if verdict_code in ("OPTIMAL_Q8", "OPTIMAL_Q4", "TIGHT_FIT_4K") else (
        layers_str.split("/")[0] if verdict_code == "PARTIAL_OFFLOAD" else "0"
    )
    ctx_flag = "4096" if verdict_code == "TIGHT_FIT_4K" else "8192"

    cli_ollama = f"ollama run {mod['ollama']}"
    cli_llamacpp = f"llama-cli -hf {mod['hf_repo']}-GGUF:Q4_K_M -ngl {ngl_flag} -c {ctx_flag} -fa"

    return {
        "slug": f"{hw['slug']}-run-{mod['slug']}",
        "vram_q4_km_gb": vram_q4_km,
        "vram_q5_km_gb": vram_q5_km,
        "vram_q8_0_gb": vram_q8_0,
        "vram_fp16_gb": vram_fp16,
        "kv_cache_8k_gb": kv_cache_8k,
        "kv_cache_32k_gb": kv_cache_32k,
        "total_req_8k_q4_gb": total_req_8k_q4,
        "verdict_code": verdict_code,
        "verdict_label": verdict_label,
        "est_tokens_per_sec": est_tps,
        "recommended_quant": rec_quant,
        "gpu_layers_offload": layers_str,
        "cli_ollama_cmd": cli_ollama,
        "cli_llamacpp_cmd": cli_llamacpp,
        "monetization_route": route,
        "direct_answer_capsule": capsule,
    }


def main() -> None:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        cur.executescript(f.read())

    # 1. Seed Hardware
    hw_ids: Dict[str, int] = {}
    for hw in HARDWARE_CATALOG:
        cur.execute("""
            INSERT INTO hardware (name, slug, vendor, category, vram_gb, bandwidth_gbs, tdp_watts, release_year, msrp_usd, amazon_query, cloud_gpu_equivalent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET vram_gb=excluded.vram_gb, bandwidth_gbs=excluded.bandwidth_gbs
        """, (
            hw["name"], hw["slug"], hw["vendor"], hw["category"], hw["vram_gb"],
            hw["bandwidth_gbs"], hw["tdp_watts"], hw["release_year"], hw["msrp_usd"],
            hw["amazon_query"], hw["cloud_gpu"]
        ))
        cur.execute("SELECT id FROM hardware WHERE slug = ?", (hw["slug"],))
        hw_ids[hw["slug"]] = cur.fetchone()[0]

    # 2. Fetch Live Config dari Hugging Face API + Seed Models
    print(f"Memvalidasi metadata arsitektur {len(MODEL_CATALOG)} model dari Hugging Face Hub...")
    model_ids: Dict[str, int] = {}
    live_hits = 0
    for mod in MODEL_CATALOG:
        cfg = fetch_hf_config(mod["hf_repo"])
        if cfg:
            live_hits += 1
            mod["layers"] = int(cfg.get("num_hidden_layers", mod["layers"]))
            mod["kv_heads"] = int(cfg.get("num_key_value_heads", cfg.get("num_attention_heads", mod["kv_heads"])))
            if "head_dim" in cfg and cfg["head_dim"]:
                mod["head_dim"] = int(cfg["head_dim"])
            elif "hidden_size" in cfg and "num_attention_heads" in cfg and cfg["num_attention_heads"]:
                mod["head_dim"] = int(cfg["hidden_size"] // cfg["num_attention_heads"])
            if "max_position_embeddings" in cfg and cfg["max_position_embeddings"]:
                mod["max_context"] = int(cfg["max_position_embeddings"])

        cur.execute("""
            INSERT INTO llm_models (hf_repo_id, name, slug, family, total_params_b, active_params_b, is_moe, hidden_layers, kv_heads, head_dim, max_context, ollama_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET hidden_layers=excluded.hidden_layers, kv_heads=excluded.kv_heads, head_dim=excluded.head_dim
        """, (
            mod["hf_repo"], mod["name"], mod["slug"], mod["family"], mod["total_b"],
            mod["active_b"], mod["is_moe"], mod["layers"], mod["kv_heads"],
            mod["head_dim"], mod["max_ctx"], mod["ollama"]
        ))
        cur.execute("SELECT id FROM llm_models WHERE slug = ?", (mod["slug"],))
        model_ids[mod["slug"]] = cur.fetchone()[0]

    print(f"[HF API] {live_hits}/{len(MODEL_CATALOG)} config.json publik berhasil diverifikasi langsung.")

    # 3. Generate Matriks Hardware x Model
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    total_inserted = 0
    for hw in HARDWARE_CATALOG:
        for mod in MODEL_CATALOG:
            row = calculate_matrix_row(hw, mod)
            cur.execute("""
                INSERT INTO compatibility_matrix (
                    slug, hardware_id, model_id, vram_q4_km_gb, vram_q5_km_gb, vram_q8_0_gb, vram_fp16_gb,
                    kv_cache_8k_gb, kv_cache_32k_gb, total_req_8k_q4_gb, verdict_code, verdict_label,
                    est_tokens_per_sec, recommended_quant, gpu_layers_offload, cli_ollama_cmd,
                    cli_llamacpp_cmd, monetization_route, direct_answer_capsule, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'enriched', ?)
                ON CONFLICT(slug) DO UPDATE SET
                    total_req_8k_q4_gb=excluded.total_req_8k_q4_gb,
                    verdict_code=excluded.verdict_code,
                    est_tokens_per_sec=excluded.est_tokens_per_sec,
                    direct_answer_capsule=excluded.direct_answer_capsule,
                    updated_at=excluded.updated_at
            """, (
                row["slug"], hw_ids[hw["slug"]], model_ids[mod["slug"]],
                row["vram_q4_km_gb"], row["vram_q5_km_gb"], row["vram_q8_0_gb"], row["vram_fp16_gb"],
                row["kv_cache_8k_gb"], row["kv_cache_32k_gb"], row["total_req_8k_q4_gb"],
                row["verdict_code"], row["verdict_label"], row["est_tokens_per_sec"],
                row["recommended_quant"], row["gpu_layers_offload"], row["cli_ollama_cmd"],
                row["cli_llamacpp_cmd"], row["monetization_route"], row["direct_answer_capsule"], now_iso
            ))
            total_inserted += 1

    conn.commit()
    conn.close()
    print(f"[SUKSES] {total_inserted} halaman matriks Hardware x LLM siap di {DB_FILE}!")


if __name__ == "__main__":
    main()
