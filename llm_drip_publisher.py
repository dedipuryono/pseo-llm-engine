import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

DB_FILE = "llm_staging.db"
BATCH_SQL_FILE = "d1_llm_publish_batch.sql"
ASTRO_DATA_FILE = os.path.join("web-app", "src", "data", "llm_catalog.json")
DAILY_LIMIT = 30


def publish_next_batch(limit: int = DAILY_LIMIT, sync_remote: bool = True) -> None:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT cm.id, cm.slug, h.slug AS hw_slug, m.slug AS model_slug
        FROM compatibility_matrix cm
        JOIN hardware h ON cm.hardware_id = h.id
        JOIN llm_models m ON cm.model_id = m.id
        WHERE cm.status = 'enriched'
        ORDER BY cm.id ASC
    """)
    raw_rows = [dict(r) for r in cur.fetchall()]

    hw_counters: Dict[str, int] = {}
    interleaved = []
    for r in raw_rows:
        idx = hw_counters.get(r["hw_slug"], 0)
        hw_counters[r["hw_slug"]] = idx + 1
        interleaved.append((idx, r["model_slug"], r))
    interleaved.sort(key=lambda t: (t[0], t[1]))
    batch = [t[2] for t in interleaved[:limit]]

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    if batch:
        sql_lines = [f"-- LLM Matrix Drip Batch ({len(batch)} pages) - {now_iso} UTC"]
        for item in batch:
            cur.execute(
                "UPDATE compatibility_matrix SET status = 'published', published_at = ?, updated_at = ? WHERE id = ?",
                (now_iso, now_iso, item["id"]),
            )
            safe_slug = item["slug"].replace("'", "''")
            sql_lines.append(
                f"UPDATE compatibility_matrix SET status = 'published', published_at = '{now_iso}', "
                f"updated_at = '{now_iso}' WHERE slug = '{safe_slug}';"
            )
        conn.commit()
        with open(BATCH_SQL_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(sql_lines) + "\n")
        print(f"[OK] {len(batch)} halaman ditandai 'published' -> {BATCH_SQL_FILE}")

        if sync_remote:
            subprocess.run(
                ["npx", "wrangler", "d1", "execute", "pseo-llm-db", "--remote", f"--file={BATCH_SQL_FILE}"],
                shell=(os.name == "nt"),
                check=True,
            )
    else:
        print("Seluruh 960 halaman matriks sudah terbit.")

    export_astro_catalog(conn)
    conn.close()


def export_astro_catalog(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        SELECT cm.*, h.name AS hw_name, h.slug AS hw_slug, h.vendor AS hw_vendor,
               h.category AS hw_category, h.vram_gb, h.bandwidth_gbs, h.tdp_watts,
               h.msrp_usd, h.amazon_query, h.cloud_gpu_equivalent,
               m.hf_repo_id, m.name AS model_name, m.slug AS model_slug, m.family AS model_family,
               m.total_params_b, m.active_params_b, m.is_moe, m.hidden_layers,
               m.kv_heads, m.head_dim, m.max_context, m.ollama_tag, m.license
        FROM compatibility_matrix cm
        JOIN hardware h ON cm.hardware_id = h.id
        JOIN llm_models m ON cm.model_id = m.id
        WHERE cm.status = 'published'
        ORDER BY cm.published_at DESC, cm.id ASC
    """)
    catalog: List[Dict[str, Any]] = [dict(r) for r in cur.fetchall()]
    os.makedirs(os.path.dirname(ASTRO_DATA_FILE), exist_ok=True)
    with open(ASTRO_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"[OK] Katalog Astro diperbarui: {len(catalog)} halaman aktif -> {ASTRO_DATA_FILE}")


if __name__ == "__main__":
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else DAILY_LIMIT
    no_sync = "--no-sync" in sys.argv
    publish_next_batch(limit=batch_size, sync_remote=not no_sync)
