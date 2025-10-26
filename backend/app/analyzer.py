import pandas as pd
import io
import os
import math
import logging
from app.prompts import response
import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

IDLE_CPU_THRESHOLD = 0.20  # 20% average CPU usage, considered idle
LOW_IO_THRESHOLD = 1       # 1 IOPS, considered low
HIGH_COST_THRESHOLD = 50   # $50 monthly cost, considered high
GPU_LOW_UTIL = 0.30        # 30% GPU utilization, considered low

def parse(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(csv_text))
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def estimate_savings(row):
    """
    Accepts a dict-like row (with keys: service, monthly_cost, usage_hours, avg_cpu, avg_mem, iops, avg_gpu_util).
    Always returns: (suggestion_or_None, estimated_savings_float, confidence_str)
    """
    service = str(row.get("service", "")).lower()
    cost = float(row.get("monthly_cost") or 0)
    usage_hours = float(row.get("usage_hours") or 720)
    cpu = float(row.get("avg_cpu") or 0)
    mem = float(row.get("avg_mem") or 0)

    suggestion = None
    estimated_savings = 0.0
    confidence = "low"

    # Compute / instance suggestions
    if any(k in service for k in ("compute", "instance", "vm")):
        if cpu < IDLE_CPU_THRESHOLD and usage_hours >= 200:
            unused_fraction = 1 - (cpu / 0.5)
            unused_fraction = max(0, min(1, unused_fraction))
            estimated_savings = cost * unused_fraction * 0.5
            suggestion = "resize_instance"
            confidence = "medium" if cpu < 0.1 else "low"

    # Storage suggestions (independent)
    if "storage" in service or "bucket" in service:
        iops = float(row.get("iops") or 0)
        if iops < LOW_IO_THRESHOLD and cost > HIGH_COST_THRESHOLD:
            candidate = cost * 0.5
            if candidate > estimated_savings:
                estimated_savings = candidate
                suggestion = "move_to_cold_storage"
                confidence = "medium"

    # GPU suggestions (independent)
    if "gpu" in service or "tpu" in service:
        gpu_util = float(row.get("avg_gpu_util") or 0)
        if gpu_util < GPU_LOW_UTIL and cost > 100:
            candidate = cost * 0.5
            if candidate > estimated_savings:
                estimated_savings = candidate
                suggestion = "remove_gpu_or_schedule_batch"
                confidence = "medium"

    estimated_savings = round(float(estimated_savings), 2)
    return suggestion, estimated_savings, confidence

def summarize_findings(findings):
    # Use .get correctly on dicts; default to 0 if missing
    total_savings = sum([f.get('estimated_savings', 0) for f in findings])
    total_savings = round(total_savings, 2)
    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "total_estimated_monthly_savings": total_savings,
        "num_findings": len(findings),
        "findings": findings
    }

def analyze_billing_csv(csv_text: str):
    try:
        df = parse(csv_text)
    except Exception:
        logger.exception("Failed to parse CSV input.")
        raise

    df = df.fillna("")

    findings = []
    for idx, row in df.iterrows():
        try:
            item = {
                "service": row.get("service") or row.get("product") or "",
                "resource_name": row.get("resource_name") or row.get("resource") or str(row.get("instance_id") or ""),
                "usage_hours": float(row.get("usage_hours") or 720),
                "avg_cpu": float(row.get("avg_cpu") or 0),
                "avg_mem": float(row.get("avg_mem") or 0),
                "monthly_cost": float(row.get("monthly_cost") or 0),
                "iops": float(row.get("iops") or 0),
                "avg_gpu_util": float(row.get("avg_gpu_util") or 0),
            }

            suggestion, estimated_savings, confidence = estimate_savings(item)

            if suggestion:
                try:
                    explanation, action_cmd = response(item, suggestion, estimated_savings, confidence)
                except Exception:
                    logger.exception("LLM response failed for resource: %s", item.get("resource_name"))
                    explanation = f"{item.get('service')} resource {item.get('resource_name')} could be optimized. Consider {suggestion}."
                    action_cmd = "Manual review recommended."

                findings.append({
                    "service": item["service"],
                    "resource_name": item["resource_name"],
                    "issue": suggestion,
                    "estimated_savings": estimated_savings,
                    "confidence": confidence,
                    "explanation": explanation,
                    "action_command": action_cmd
                })
        except Exception:
            logger.exception("Failed processing row index %s", idx)
            continue

    return summarize_findings(findings)
