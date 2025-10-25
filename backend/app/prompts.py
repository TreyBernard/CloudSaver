import os 
import openai
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

llm_Model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def response(item, key, savings, confidence):
    """
    returns: explanation, action command
    """
    service = item.get("service","Unknown Service")
    resource = item.get("resource_name","unknown")
    cpu = item.get("avg_cpu",0)
    mem = item.get("avg_mem",0)
    cost = item.get("monthly_cost",0)

    mapping = {
        "resize_instance": "Resize the instance to a small machine type (reduce CPU/memory).",
        "move_to_cold_storage": "Move infrequently accesed data to cold storage class (Nearline/Coldline/Archive).",
        "remove_unused_resources": "Delete GPU from this instance or schedule the workload to run in batch on demand.",
    }
    suggestion = mapping.get(key, key)

    prompt = f"""
You are a cloud cost optimization expert and FinOps assistant. Given the following resource summary generate:
1. A concise one paragraph plain English explanation of why this resource is innefficient.
2. A short, concise actionable reccomendation (ideal CLI) or single step by step instruction an engineer can run to fix this issue.
3. A conservative estimate sentence that repeats the estimated monthly savings ${savings} and explains confidence level{confidence}.
Return JSON with keys: explanation, action command.

Resource:
- Service: {service}
- Resource Name: {resource}
- Average CPU Utilization: {cpu}%
- Average Memory Utilization: {mem}%
- Monthly Cost: ${cost}

Suggested Fix: {suggestion}
Be consise, factual, and avoid any fluff, so stay conservative. If you are not sure, say 'uncertain' and recommend manual review of the data.
"""
    
    try:
        res = openai.ChatCompletion.create(
            model = llm_Model,
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 300,
            temperature = 0.2,
        )
        text = res["choices"][0]["message"]["content"].strip()
    except Exception as e:
        explanation = f"{service} resource {resource} could be optimized. Consider {suggestion}."
        action = "Please review the resource and resize, or change storage as appropriate."
        return explanation, action
    
    import json
    try:
        cleaned = text
        if cleaned.startswith("{"):
            data = json.loads(cleaned)
            return data.get("explanation",""), data.get("action command","")
        else:
            lines = text.splitlines()
            explanation = "\n".join(lines[:3])
            action = "\n".join(lines[3:6]) if len(lines) > 3 else suggestion
            return explanation, action
    except Exception:
        return text, suggestion