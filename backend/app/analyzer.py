import pandas as pd
import io
import os
import csv
import logging
from app.prompts import response
import datetime
import re

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

#thresholds
IDLE_CPU_THRESHOLD = 0.20  
LOW_IO_THRESHOLD = 1
HIGH_COST_THRESHOLD = 50
GPU_LOW_UTIL = 0.30

INR_TO_USD = float(os.getenv("INR_TO_USD", "0.012"))

#Map common header names (after lower+underscore) to normalized keys
COLUMN_ALIASES = {
    "service_name": "service",
    "service": "service",
    "product": "service",
    "resource_id": "resource_name",
    "resource_name": "resource_name",
    "resource": "resource_name",
    "instance_id": "resource_name",
    "usage_quantity": "usage_hours",
    "usage_hours": "usage_hours",
    "cpu_utilization_(%)": "avg_cpu",
    "cpu_utilization": "avg_cpu",
    "cpu_utilization_%": "avg_cpu",
    "avg_cpu": "avg_cpu",
    "memory_utilization_(%)": "avg_mem",
    "memory_utilization": "avg_mem",
    "avg_mem": "avg_mem",
    "total_cost_(inr)": "monthly_cost",
    "total_cost": "monthly_cost",
    "rounded_cost": "monthly_cost",
    "unrounded_cost": "monthly_cost",
    "monthly_cost": "monthly_cost",
    "cost": "monthly_cost",
    "cost_per_quantity_($)": "monthly_cost",
    "iops": "iops",
    "avg_gpu_util": "avg_gpu_util",
    "gpu_utilization": "avg_gpu_util",
    "gpu_utilization_(%)": "avg_gpu_util",
}

def clean_num(x):
    if x is None:
        return 0.0
    s = str(x).strip()

    if s == "" or s.lower() in ("nan", "none"):
        return 0.0
    
    s = s.replace(",", "").replace("₹", "").replace("$", "").strip()
    
    y = re.search(r"-?\d+(\.\d+)?", s)
    if y:
        try:
            return float(y.group(0))
        except Exception:
            return 0.0
    return 0.0

def percent_to_fraction(x):
    v = clean_num(x)
    if 0 <= v <= 1:
        return v
    return v / 100.0

def normalize_row(row_dict):
    normalized = {
        "service": "",
        "resource_name": "",
        "usage_hours": 0.0,
        "avg_cpu": 0.0,
        "avg_mem": 0.0,
        "monthly_cost": 0.0,
        "iops": 0.0,
        "avg_gpu_util": 0.0,
    }

    for raw_key_orig, raw_val in row_dict.items():
        if raw_key_orig is None:
            continue
        raw_key = str(raw_key_orig).strip()
        key = raw_key.lower().replace(" ", "_").replace("-", "_")
        mapped = COLUMN_ALIASES.get(key)
        if not mapped:
            if "cpu" in key and mapped is None:
                mapped = "avg_cpu"
            elif "memory" in key and mapped is None:
                mapped = "avg_mem"
            elif "cost" in key and mapped is None:
                mapped = "monthly_cost"

        if not mapped:
            continue

        if mapped == "service":
            normalized["service"] = str(raw_val)
        elif mapped == "resource_name":
            normalized["resource_name"] = str(raw_val)
        elif mapped == "usage_hours":
            normalized["usage_hours"] = clean_num(raw_val)
        elif mapped == "avg_cpu":
            normalized["avg_cpu"] = percent_to_fraction(raw_val)
        elif mapped == "avg_mem":
            normalized["avg_mem"] = percent_to_fraction(raw_val)
        elif mapped == "monthly_cost":
            val = clean_num(raw_val)
            if "inr" in key or "rs" in key or "rupee" in key or "₹" in str(raw_key_orig).lower():
                val = val * INR_TO_USD
            normalized["monthly_cost"] = val
        elif mapped == "iops":
            normalized["iops"] = clean_num(raw_val)
        elif mapped == "avg_gpu_util":
            normalized["avg_gpu_util"] = percent_to_fraction(raw_val)

    if normalized["usage_hours"] == 0:
        normalized["usage_hours"] = 720 
    return normalized

def parse(csv_text: str) -> pd.DataFrame:
    text = csv_text.lstrip("\ufeff")
    delim = ","
    try:
        sample = "\n".join(text.splitlines()[:10])
        dialect = csv.Sniffer().sniff(sample)
        delim = dialect.delimiter
    except Exception:
        delim = ","

    try:
        df = pd.read_csv(io.StringIO(text), delimiter=delim)
    except Exception:
        df = pd.read_csv(io.StringIO(text))

    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    logger.info("Parsed CSV columns (raw): %s (delimiter=%s)", df.columns.tolist(), delim)
    try:
        logger.info("CSV head (sample): %s", df.head().to_dict(orient="records")[:3])
    except Exception:
        logger.exception("Failed to log df.head()")
    return df

def estimate_savings(item):

    service = str(item.get("service", "")).lower()
    cost = float(item.get("monthly_cost") or 0)
    usage_hours = float(item.get("usage_hours") or 720)
    cpu = float(item.get("avg_cpu") or 0)
    mem = float(item.get("avg_mem") or 0)
    iops = float(item.get("iops") or 0)

    suggestion = None
    estimated_savings = 0.0
    confidence = "low"

    if any(k in service for k in ("compute", "instance", "vm", "dataproc", "gce", "computeengine", "ec2")):
        if cpu < IDLE_CPU_THRESHOLD and usage_hours >= 200 and cost > HIGH_COST_THRESHOLD:
            unused_fraction = 1 - (cpu / 0.5) 
            unused_fraction = max(0.1, min(0.9, unused_fraction))
            estimated_savings = cost * unused_fraction * 0.5
            suggestion = "resize_instance"
            confidence = "medium" if cpu < 0.1 else "low"

    if any(k in service for k in ("cloud_storage", "storage", "bucket", "filestore")):
        if iops < LOW_IO_THRESHOLD and cost > HIGH_COST_THRESHOLD:
            candidate = cost * 0.5 
            if candidate > estimated_savings:
                estimated_savings = candidate
                suggestion = "move_to_cold_storage"
                confidence = "medium"

    if "bigquery" in service:
        if cost > (HIGH_COST_THRESHOLD * 5): 
            candidate = cost * 0.2 
            if candidate > estimated_savings:
                estimated_savings = candidate
                suggestion = "review_bigquery_optimization" 
                confidence = "low"

    if any(k in service for k in ("gpu", "tpu")) or float(item.get("avg_gpu_util") or 0) > 0:
        gpu_util = float(item.get("avg_gpu_util") or 0)
        if gpu_util < GPU_LOW_UTIL and cost > 100:
            candidate = cost * 0.5
            if candidate > estimated_savings:
                estimated_savings = candidate
                suggestion = "remove_gpu_or_schedule_batch"
                confidence = "medium"

    estimated_savings = round(float(estimated_savings or 0.0), 2)
    return suggestion, estimated_savings, confidence

def summarize_findings(findings):
    total_savings = sum([f.get('estimated_savings', 0) for f in findings])
    total_savings = round(total_savings, 2)
    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "total_estimated_monthly_savings": total_savings,
        "num_findings": len(findings),
        "findings": findings
    }

def analyze_billing_csv(csv_text: str):
    df = parse(csv_text)
    if df.shape[0] == 0:
        logger.info("Parsed DataFrame is empty.")
        return summarize_findings([])

    findings = []
    for idx, row in df.iterrows():
        try:
            raw = row.to_dict()
            item = normalize_row(raw)

            suggestion, estimated_savings, confidence = estimate_savings(item)
            if suggestion:
                try:
                    explanation, action_cmd = response(item, suggestion, estimated_savings, confidence)
                except Exception:
                    logger.exception("LLM response failed for resource: %s", item.get("resource_name"))
                    explanation = f"{item.get('service')} resource {item.get('resource_name')} could be optimized. Consider {suggestion}."
                    action_cmd = "Manual review recommended."

                findings.append({
                    "service": item.get("service") or "",
                    "resource_name": item.get("resource_name") or "",
                    "issue": suggestion,
                    "estimated_savings": estimated_savings,
                    "confidence": confidence,
                    "explanation": explanation,
                    "action_command": action_cmd
                })
        except Exception:
            logger.exception("Failed processing row %s", idx)
            continue

    return summarize_findings(findings)
