import pandas as pd
import io
import os
import math
from prompts import generate_llm_explanation
import datetime

IDLE_CPU_THRESHOLD = 0.20 # 20% avergage CPU usage, considered idle
LOW_IO_THRESHOLD = 1 # 1 IOPS, considered low
HIGH_COST_THRESHOLD = 50 # $50 monthly cost, considered high
GPU_LOW_UTIL = 0.30 # 30% GPU utilization, considered low

def parse(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(csv_text))
    df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
    return df

def safe_get(df, col, default=None):
    return df[col] if col in df.columns else pd.Series([default]*len(df))

def estimate_savings(row):
    service = str(row.get("service", "")).lower()
    cost = float(row.get("monthyly_cost", 0) or 0)
    usage_hours = float(row.get("usage_hours", 720) or 720)
    cpu = float(row.get("avgcpu", 0) or 0)
    mem = float(row.get("avg_mem", 0) or 0)

    suggestion = None
    estimate_savings = 0.0
    confindence = "low"

    if "compute" in service or "instance" in service or "vm" in service:
        if cpu < IDLE_CPU_THRESHOLD and usage_hours >= 200:
            unused_fraction = 1- (cpu / 0.5)
            unused_fraction = max(0, min(1, unused_fraction))
            estimated_savings = cost * unused_fraction * 0.5
            suggestion = "resize_instance"
            confidence = "medium" if cpu < 0.1 else "low"
        elif "storage" in service or "bucket" in service:
            iops = float(row.get("iops", 0) or 0)
            if iops < LOW_IO_THRESHOLD and cost > HIGH_COST_THRESHOLD:
                estimated_savings = cost * 0.5
                suggestion = "move_to_cold_storage"
                confidence = "medium"
        elif "gpu" in service or "tpu" in service:
            gpu_util = float(row.get("avg_gpu_util", 0) or 0)
            if gpu_util < GPU_LOW_UTIL and cost > 100:
                estimated_savings = cost * 0.5
                suggestion = "remove_gpu_or_schedule_batch"
                confidence = "medium"
        
        estimate_savings = round(float(estimated_savings), 2)
        return suggestion, estimated_savings, confidence
    
    def summarize_findings(findings):
        total_savings = sum([f['estimated_savings'] for f in findings])
        total_savings = round(total_savings, 2)
        return {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "total_estimated_monthly_savings": total_savings,
            "num_findings": len(findings),
            "findings": findings
        }
    
    def analyze_billing_csv(csv_text: str):
        df = parse(csv_text)
        df = df.fillna("")
        findings = []
        for _, row in df.iterrows():
            item = {
                "service": row.get("service") or row.get("product") or "",
                "resource_name": row.get("resource_name") or row.get("resource") or str(row.get("instance_id") or ""),
                "usage_hours": float(row.get("usage_hours") or 720),
                "avg_cpu": float(row.get("avg_cpu") or 0),
                "avg_mem": float(row.get("avg_mem") or 0),
                "monthyly_cost": float(row.get("monthyly_cost") or 0),
                "iops": float(row.get("iops") or 0),
                "avg_gpu_util": float(row.get("avg_gpu_util") or 0),
            }

            suggestion, estimated_savings, confidence = estimate_savings(item)
            if suggestion:
                explanation, action_cmd = generate_llm_explanation(item, suggestion, estimate_savings, confidence)
                findings.append = ({
                    "service": item["service"],
                    "resource_name": item["resource_name"],
                    "issue": suggestion,
                    "estimated_savings": estimated_savings,
                    "confidence": confidence,
                    "explanation": explanation,
                    "action_command": action_cmd
                })
        return summarize_findings(findings)