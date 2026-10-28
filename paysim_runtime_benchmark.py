#!/usr/bin/env python3
"""Collect PaySim fork Docker runtime and a bounded, reproducible run.

Run from the repository root with Python 3.10+. Standard library only.
Read-only snapshot: python paysim_runtime_benchmark.py snapshot
Finite run:        python paysim_runtime_benchmark.py bench --events 5000

The finite run stops the regular replayer, but never deletes containers or volumes.
It uses `docker compose run --rm` for one-off replay with a unique RUN_ID.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from statistics import mean
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path.cwd()
OUT_ROOT = ROOT / "_paysim_exports"
COMPOSE = ["docker", "compose", "-f", "docker-compose.yml"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run(command: list[str], *, timeout: int = 90, check: bool = False) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                errors="replace", timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        if check:
            raise RuntimeError(f"Cannot run {' '.join(command[:4])}: {exc}") from exc
        return subprocess.CompletedProcess(command, 127, "", str(exc))
    if check and result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command[:5])}\n{result.stderr[-1000:]}")
    return result


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", errors="replace")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def checked_docker() -> None:
    global COMPOSE
    if not (ROOT / "docker-compose.yml").exists():
        raise RuntimeError("Open a terminal inside the paysim-big-data-baseline repository root.")
    if not shutil.which("docker"):
        raise RuntimeError("Docker CLI not found. Start Docker Desktop and retry.")
    run(["docker", "info", "--format", "{{.MemTotal}}"], check=True)
    if docker_memory() < 5_500_000_000 and (ROOT / "docker-compose.low-memory.yml").exists():
        COMPOSE = COMPOSE + ["-f", "docker-compose.low-memory.yml"]


def docker_memory() -> int:
    value = run(["docker", "info", "--format", "{{.MemTotal}}"], check=True).stdout.strip()
    return int(value)


def mongosh(code: str, *, timeout: int = 70) -> object:
    command = COMPOSE + ["exec", "-T", "mongodb", "mongosh", "--quiet", "--eval", code]
    response = run(command, timeout=timeout, check=True)
    # Docker and mongosh may add harmless status lines. JSON is on the last JSON line.
    for line in reversed(response.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise RuntimeError("mongosh returned no JSON: " + response.stdout[-800:])


def mongo_snapshot(run_id: str | None) -> object:
    # No raw transactions, ground-truth labels, secrets, or complete dataset are exported.
    rid = json.dumps(run_id)
    code = """
const d = db.getSiblingDB('paysim');
const rid = RID;
const current = rid ? d.runs.findOne({_id:rid}) : d.runs.find().sort({started_at:-1}).limit(1).next();
const k = current ? current.run_id : null;
const m = k ? d.pipeline_metrics.find({run_id:k},{_id:0}).sort({batch_id:1}).limit(400).toArray() : [];
const out = {
  collected_at: new Date(), run_id: k, run: current,
  evaluation: k ? d.evaluation_totals.findOne({_id:k}) : null,
  pipeline_metrics: m,
  live_aggregates: k ? d.live_aggregates.find({run_id:k},{_id:0}).toArray() : [],
  counts: k ? {
    fraud_alerts: d.fraud_alerts.countDocuments({run_id:k}),
    recent_transactions: d.recent_transactions.countDocuments({run_id:k}),
    ground_truth: d.ground_truth.countDocuments({run_id:k}),
    microbatches_exported: m.length
  } : {},
  system_metrics: d.system_metrics.findOne({_id:'spark'}),
  indexes: {
    fraud_alerts: d.fraud_alerts.getIndexes().map(x=>({name:x.name,key:x.key})),
    pipeline_metrics: d.pipeline_metrics.getIndexes().map(x=>({name:x.name,key:x.key})),
    recent_transactions: d.recent_transactions.getIndexes().map(x=>({name:x.name,key:x.key}))
  }
};
print(JSON.stringify(out));
""".replace("RID", rid)
    return mongosh(code)


def mongo_progress(run_id: str) -> dict:
    rid = json.dumps(run_id)
    code = """
const d=db.getSiblingDB('paysim'); const id=RID;
const r=d.runs.findOne({_id:id}) || {};
const e=d.evaluation_totals.findOne({_id:id}) || {};
print(JSON.stringify({status:r.status || 'not_found', emitted:r.events_emitted || 0,
  source_rows:r.source_rows || 0, processed:e.processed || 0,
  ground_truth_missing:e.ground_truth_missing || 0, delivery_errors:r.delivery_errors || 0}));
""".replace("RID", rid)
    value = mongosh(code)
    if not isinstance(value, dict):
        raise RuntimeError("Unexpected progress data")
    return value


def save_command(folder: Path, filename: str, command: list[str], *, timeout: int = 90) -> str:
    value = run(command, timeout=timeout)
    content = f"$ {' '.join(command)}\n(exit={value.returncode})\n{value.stdout}\n{value.stderr}"
    write_text(folder / filename, content)
    return value.stdout


def container_ids() -> list[str]:
    response = run(COMPOSE + ["ps", "-q", "kafka", "namenode", "datanode", "mongodb", "spark", "replayer", "streamlit"])
    return [x.strip() for x in response.stdout.splitlines() if re.fullmatch(r"[0-9a-f]{12,64}", x.strip())]


def docker_stats() -> list[dict]:
    ids = container_ids()
    if not ids:
        return []
    response = run(["docker", "stats", "--no-stream", "--format", "{{json .}}"] + ids, timeout=45)
    items = []
    for line in response.stdout.splitlines():
        try:
            items.append(json.loads(line))
        except ValueError:
            continue
    return items


def dashboard_query_benchmark() -> dict:
    # Measures the MongoDB-backed snapshot loader, NOT full browser paint time.
    code = """
import json, time
from dashboard_core import load_snapshot
load_snapshot()  # warm up MongoDB connection and Streamlit cache
samples = []
for _ in range(20):
    started = time.perf_counter()
    result = load_snapshot()
    elapsed_ms = (time.perf_counter() - started) * 1000
    if result is not None:
        samples.append({"wall_clock_ms": elapsed_ms, "internal_query_ms": result.query_latency_ms,
                        "run_id": result.run_id, "freshness_seconds": result.freshness})
print("PAYSIM_QUERY_BENCH=" + json.dumps({"samples": samples, "sample_count": len(samples)}))
"""
    command = COMPOSE + ["exec", "-T", "streamlit", "python", "-c", code]
    result = run(command, timeout=150, check=True)
    marker = "PAYSIM_QUERY_BENCH="
    for line in reversed(result.stdout.splitlines()):
        if line.startswith(marker):
            data = json.loads(line[len(marker):])
            samples = data.get("samples", [])
            internal = [float(x["internal_query_ms"]) for x in samples]
            elapsed = [float(x["wall_clock_ms"]) for x in samples]
            data["internal_query_p50_ms"] = percentile(internal, 50)
            data["internal_query_p95_ms"] = percentile(internal, 95)
            data["wall_clock_p50_ms"] = percentile(elapsed, 50)
            data["wall_clock_p95_ms"] = percentile(elapsed, 95)
            data["measurement_scope"] = "20 serial calls to dashboard_core.load_snapshot() inside Streamlit container; not full browser render"
            return data
    raise RuntimeError("No dashboard query benchmark result: " + result.stdout[-500:])


def runtime_capture(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    save_command(folder, "git_commit.txt", ["git", "rev-parse", "HEAD"])
    save_command(folder, "git_status.txt", ["git", "status", "--short"])
    save_command(folder, "docker_version.txt", ["docker", "version", "--format", "client={{.Client.Version}} server={{.Server.Version}}"])
    save_command(folder, "docker_info.txt", ["docker", "info", "--format", "architecture={{.Architecture}} cpus={{.NCPU}} docker_memory_bytes={{.MemTotal}} os_type={{.OSType}}"])
    save_command(folder, "compose_ps.txt", COMPOSE + ["ps", "-a"])
    save_command(folder, "compose_images.txt", COMPOSE + ["images"])
    save_command(folder, "container_logs.txt", COMPOSE + ["logs", "--no-color", "--tail=150", "spark", "mongodb", "streamlit", "replayer"], timeout=90)
    write_json(folder / "docker_stats_instant.json", {"sampled_at": now(), "containers": docker_stats()})
    inspected = []
    for cid in container_ids():
        response = run(["docker", "inspect", "--format", "{{json .}}", cid], timeout=30)
        try:
            obj = json.loads(response.stdout)[0]
            inspected.append({"name": obj.get("Name"), "image": obj.get("Config", {}).get("Image"),
                              "state": obj.get("State"),
                              "memory_limit_bytes": obj.get("HostConfig", {}).get("Memory"),
                              "command": obj.get("Config", {}).get("Cmd")})
        except (ValueError, IndexError, TypeError):
            inspected.append({"container_id": cid, "inspection_error": response.stderr[-200:]})
    write_json(folder / "container_state.json", inspected)
    write_json(folder / "host_runtime.json", {"collected_at": now(), "python": platform.python_version(),
                                                "os": platform.system(), "docker_memory_bytes": docker_memory(),
                                                "paysim_csv_bytes": (ROOT / "data" / "paysim.csv").stat().st_size if (ROOT / "data" / "paysim.csv").exists() else None})


def percentile(values: list[float], pct: int):
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * pct / 100.0
    low = int(index)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (index - low)


def summarize(data: dict) -> dict:
    metrics = data.get("pipeline_metrics") or []
    ev = data.get("evaluation") or {}
    run_doc = data.get("run") or {}
    duration = [float(m["batch_duration_seconds"]) for m in metrics if m.get("batch_duration_seconds") is not None]
    rows = [int(m.get("processed_rows") or 0) for m in metrics]
    candidate = [float(m["processing_throughput"]) for m in metrics if m.get("processing_throughput") is not None]
    last = metrics[-1] if metrics else {}
    count = int(run_doc.get("unique_events_emitted") or 0)
    processed = int(ev.get("processed") or 0)
    return {
        "run_id": data.get("run_id"), "run_status": run_doc.get("status"),
        "emitted": run_doc.get("events_emitted"), "unique_events_emitted": count,
        "processed": processed, "ground_truth_missing": ev.get("ground_truth_missing"),
        "delivery_errors": run_doc.get("delivery_errors"),
        "processed_equals_emitted_unique": processed == count if count else None,
        "fraud_alerts": (data.get("counts") or {}).get("fraud_alerts"),
        "batch_count_exported": len(metrics),
        "total_processed_rows_in_exported_batches": sum(rows),
        "batch_duration_seconds_p50": percentile(duration, 50),
        "batch_duration_seconds_p95": percentile(duration, 95),
        "mean_processing_throughput_ev_s": mean(candidate) if candidate else None,
        "latest_processing_throughput_ev_s": last.get("processing_throughput"),
        "latest_end_to_end_latency_p95_ms": last.get("latency_p95_ms"),
        "latest_ingest_latency_p95_ms": last.get("ingest_latency_p95_ms"),
        "latest_consumer_lag": last.get("consumer_lag"),
        "latest_small_file_count": last.get("small_file_count"),
        "latest_storage_bytes": last.get("storage_size_bytes"),
        "note": "Values are raw run telemetry from this fork, not independently measured UI response-time benchmarks. Latest p95 is per last micro-batch. The exported batch list is capped at 400."
    }


def zip_folder(folder: Path) -> Path:
    destination = folder.with_suffix(".zip")
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(folder.parent))
    return destination


def snapshot_action() -> Path:
    folder = OUT_ROOT / ("runtime-" + stamp())
    runtime_capture(folder / "runtime")
    try:
        data = mongo_snapshot(None)
        write_json(folder / "mongodb_snapshot.json", data)
        if isinstance(data, dict):
            write_json(folder / "summary.json", summarize(data))
    except Exception as e:
        write_text(folder / "mongodb_error.txt", str(e))
    try:
        write_json(folder / "dashboard_query_benchmark.json", dashboard_query_benchmark())
    except Exception as e:
        write_text(folder / "dashboard_query_error.txt", str(e))
    return zip_folder(folder)


def record_sample(folder: Path, stage: str, rid: str) -> None:
    entry = {"time_utc": now(), "stage": stage, "docker_stats": docker_stats()}
    try:
        entry["mongo_progress"] = mongo_progress(rid)
    except Exception as exc:
        entry["mongo_error"] = str(exc)
    with (folder / "samples.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(entry, default=str) + "\n")
    p = entry.get("mongo_progress") or {}
    print(f"  {stage}: emitted={p.get('emitted', '?')} processed={p.get('processed', '?')} status={p.get('status', '?')}", flush=True)


def bench_action(args: argparse.Namespace) -> Path:
    folder = OUT_ROOT / ("benchmark-" + stamp())
    folder.mkdir(parents=True, exist_ok=True)
    rid = "bench-" + stamp() + "-" + str(os.getpid())
    rate = args.rate if args.rate is not None else (10 if docker_memory() < 5_500_000_000 else 50)
    payload = {"run_id": rid, "started_at": now(), "events": args.events, "rate": rate,
               "start_row": args.start_row, "seed": args.seed,
               "injected_fault_rates": {"duplicate": 0, "null": 0, "late": 0},
               "selected_by": "finite, one-off Docker Compose replayer",
               "docker_memory_mode_guess": "low_memory" if docker_memory() < 5_500_000_000 else "standard",
               "timeout_seconds": args.timeout,
               "note": "Regular replayer will remain stopped after benchmark. Start it later via docker compose start replayer if needed."}
    write_json(folder / "run_configuration.json", payload)
    print("Saving Docker runtime metadata...", flush=True)
    runtime_capture(folder / "runtime_before")
    print("Stopping regular replay (Spark/MongoDB/HDFS/Kafka remain running)...", flush=True)
    run(COMPOSE + ["stop", "replayer"], timeout=75, check=True)
    p = run(COMPOSE + ["ps", "-q", "spark"])
    if not p.stdout.strip():
        write_text(folder / "ERROR.txt", "Spark container not found. Run start.sh/start.bat first.")
        return zip_folder(folder)
    command = COMPOSE + ["run", "--rm", "--no-deps", "-e", f"RUN_ID={rid}",
                         "-e", f"MAX_EVENTS={args.events}", "-e", f"EVENTS_PER_SECOND={rate}",
                         "-e", "LOOP_DATASET=false", "-e", f"START_ROW={args.start_row}",
                         "-e", f"RANDOM_SEED={args.seed}",
                         "-e", "DUPLICATE_RATE=0", "-e", "NULL_RATE=0", "-e", "LATE_EVENT_RATE=0", "replayer"]
    write_text(folder / "command.txt", "docker compose run --rm --no-deps (unique RUN_ID, bounded MAX_EVENTS, no fault injection)\n")
    run_status = None
    with (folder / "replayer_run.log").open("w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, text=True, errors="replace")
        begun = time.monotonic()
        print(f"One-off replay started: {rid}, {args.events} rows at {rate:g} ev/s", flush=True)
        try:
            while proc.poll() is None:
                if time.monotonic() - begun > args.timeout:
                    proc.terminate()
                    try:
                        proc.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    raise RuntimeError("Timed out during replay. See replayer_run.log")
                record_sample(folder, "replaying", rid)
                time.sleep(args.poll)
            run_status = proc.returncode
        except KeyboardInterrupt:
            proc.terminate()
            raise
    print(f"Replayer exit code: {run_status}. Waiting for Spark to process the run...", flush=True)
    if run_status:
        write_text(folder / "replay_error.txt", f"One-off replayer exit code: {run_status}\nCheck replayer_run.log and runtime logs.\n")
    deadline = time.monotonic() + args.timeout
    drained = False
    while time.monotonic() < deadline:
        try:
            prog = mongo_progress(rid)
            target = int(prog.get("source_rows") or 0)
            if target > 0 and prog.get("status") in {"completed", "completed_with_errors"} and int(prog.get("processed") or 0) >= target:
                drained = True
                break
        except Exception:
            pass
        record_sample(folder, "draining", rid)
        time.sleep(args.poll)
    write_json(folder / "completion.json", {"run_id": rid, "spark_caught_up": drained, "observed_at": now(),
                                            "replayer_exit_code": run_status})
    if not drained:
        print("WARNING: Spark did not catch up before the deadline; metrics may be incomplete.", flush=True)
    try:
        data = mongo_snapshot(rid)
        write_json(folder / "mongodb_snapshot.json", data)
        if isinstance(data, dict):
            write_json(folder / "summary.json", summarize(data))
    except Exception as exc:
        write_text(folder / "mongodb_error.txt", str(exc))
    runtime_capture(folder / "runtime_after")
    try:
        write_json(folder / "dashboard_query_benchmark.json", dashboard_query_benchmark())
    except Exception as e:
        write_text(folder / "dashboard_query_error.txt", str(e))
    return zip_folder(folder)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect PaySim runtime and finite benchmark ZIP (no reset / deletion).")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("snapshot", help="Read-only export of current runtime and latest MongoDB run")
    bench = sub.add_parser("bench", help="Stop regular replay; run bounded one-off replay and collect evidence")
    bench.add_argument("--events", type=int, default=5000, help="Number of PaySim rows to replay (default 5000)")
    bench.add_argument("--rate", type=float, default=None, help="Events/second; default 50 or 10 if low-memory")
    bench.add_argument("--start-row", type=int, default=1, help="PaySim source row to start from")
    bench.add_argument("--seed", type=int, default=2026)
    bench.add_argument("--poll", type=int, default=15, help="Sampling interval in seconds")
    bench.add_argument("--timeout", type=int, default=1800, help="Timeout for each replay/drain phase")
    args = parser.parse_args()
    try:
        checked_docker()
        if args.command == "bench" and (args.events < 1 or args.poll < 3 or args.timeout < 60 or args.start_row < 1):
            parser.error("events >= 1, poll >= 3, timeout >= 60 and start-row >= 1 required")
        result = snapshot_action() if args.command == "snapshot" else bench_action(args)
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)
    print("\nZIP CREATED:", result.resolve(), flush=True)
    print("Upload this ZIP to the ChatGPT project conversation. Review logs for secrets first.", flush=True)
    if args.command == "bench":
        print("Note: regular replayer is intentionally STOPPED; other services keep running.", flush=True)


if __name__ == "__main__":
    main()
