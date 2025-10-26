# app/prompts.py
import os 
from openai import AsyncOpenAI 
from dotenv import load_dotenv
import json
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") 
llm_Model = os.getenv("LLM_MODEL", "gpt-4o-mini") 
llm_Base_Url = os.getenv("LLM_BASE_URL")

client = None
if api_key:
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=llm_Base_Url if llm_Base_Url else None,
        )
    except Exception as e:
        print(f"Failed to initialize AsyncOpenAI client: {e}")

async def response(item, key, savings, confidence):
    """
    Generate an explanation and action command from the LLM based on a resource finding.
    returns: explanation, action command
    """
    if not client:
        return "LLM service not initialized. Check OPENAI_API_KEY.", "Manual review recommended."
        
    service = item.get("service","Unknown Service")
    resource = item.get("resource_name","unknown")
    cpu = item.get("avg_cpu",0)
    mem = item.get("avg_mem",0)
    cost = item.get("monthly_cost",0)

    mapping = {
        "resize_instance": "Resize the instance to a small machine type (reduce CPU/memory).",
        "move_to_cold_storage": "Move infrequently accesed data to cold storage class (Nearline/Coldline/Archive).",
        "remove_gpu_or_schedule_batch": "Delete GPU from this instance or schedule the workload to run in batch on demand.",
    }
    suggestion = mapping.get(key, key)

    prompt = f"""
You are a cloud cost optimization expert and FinOps assistant. Given the following resource summary generate:
1. A concise one paragraph plain English explanation of why this resource is innefficient.
2. A short, concise actionable reccomendation (ideal CLI) or single step by step instruction (around 2-5 sentences) an engineer can run to fix this issue.
3. A conservative estimate sentence that repeats the estimated monthly savings ${savings} and explains confidence level{confidence}.
Return JSON with keys: explanation, action command.

Resource:
- Service: {service}
- Resource Name: {resource}
- Average CPU Utilization: {round(cpu*100, 2)}%
- Average Memory Utilization: {round(mem*100, 2)}%
- Monthly Cost: ${round(cost, 2)}

Suggested Fix: {suggestion}
Use clear, professional, and simple English suitable for a technical report. Be consise, factual, and avoid any fluff, so stay conservative. If you are not sure, say 'uncertain' and recommend manual review of the data.
"""
    
    try:
        res = await client.chat.completions.create( 
            model = llm_Model,
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 300,
            temperature = 0.2,
            response_format={"type": "json_object"} 
        )
        text = res.choices[0].message.content.strip() 
    except Exception as e:
        print(f"OpenAI API call failed: {e}")
        explanation = f"{service} resource {resource} could be optimized. Consider {suggestion}."
        action = "Please review the resource and resize, or change storage as appropriate."
        return explanation, action
    
    try:
        data = json.loads(text)
        return data.get("explanation",""), data.get("action command","")
    except Exception:
        print("Failed to parse LLM response as JSON.")
        return text, suggestion
