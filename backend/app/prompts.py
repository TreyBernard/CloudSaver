import os
import openai
import json
import re
from dotenv import load_dotenv
from openai import OpenAI 

load_dotenv()

try:
    client = OpenAI()
except openai.OpenAIError:
    print("Make sure OPENAI_API_KEY is set.")
    client = None

llm_Model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def response(item, key, savings, confidence):
    if not client:
        #Handle case where client failed to initialize
        explanation = "OpenAI client initialization failed, check server logs and API key"
        action_plan = "The OpenAI API key or connection is not configured correctly, check back in logs"
        return explanation, action_plan

    service = item.get("service", "Unknown Service")
    resource = item.get("resource_name", "unknown")
    cpu = item.get("avg_cpu", 0) * 100 
    mem = item.get("avg_mem", 0) * 100 
    cost = item.get("monthly_cost", 0)

    mapping = {
        "resize_instance": f"Rightsizing (e.g., downsize instance type) for a VM with low CPU ({cpu:.1f}%) and Memory ({mem:.1f}%) utilization.",
        "move_to_cold_storage": "Move infrequently accessed data to a cheaper storage class (e.g., Nearline/Coldline/Archive).",
        "remove_gpu_or_schedule_batch": "Remove an underutilized GPU or switch to on-demand batch processing.",
        "review_bigquery_optimization": "Review BigQuery table for optimization. Check partitioning, clustering, or if data qualifies for long-term storage.",
    }
    suggestion = mapping.get(key, key)

    prompt = f"""
You are an expert Google Cloud (GCP) and AWS FinOps assistant. Your task is to provide a clear, actionable optimization plan for an engineer.
You MUST return ONLY a single, valid JSON object with two keys: "explanation" and "action_plan". Do not include any text before or after the JSON.

Given the following resource summary:
- Service: {service}
- Resource Name: {resource}
- Average CPU Utilization: {cpu:.1f}%
- Average Memory Utilization: {mem:.1f}%
- Monthly Cost: ${cost:.2f}
- Suggested Fix: {suggestion}
- Estimated Monthly Savings: ${savings:.2f}
- Confidence: {confidence}

Generate the following:
1. "explanation": A concise, one-paragraph explanation of *why* this resource is inefficient, referencing its specific metrics.
2. "action_plan": A detailed, step-by-step guide for an engineer to execute this fix.
   - Use **markdown** for formatting.
   - For CLI commands (gcloud, aws-cli), provide the *exact* command in a code block. Use placeholders like '<resource_name>' or '<new_machine_type>' where appropriate.
   - For console (UI) actions, provide a numbered list of steps (e.g., "1. Navigate to the Compute Engine console...").
   - Be specific and practical.
"""
    
    try:
        res = client.chat.completions.create(
            model=llm_Model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        text = res.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in LLM response")
            
        cleaned_text = json_match.group(0)
        data = json.loads(cleaned_text)
        
        explanation = data.get("explanation", "No explanation provided.")
        action_plan = data.get("action_plan", "No action plan provided. Manual review recommended.")
        
        return explanation, action_plan

    except Exception as e:
        print(f"Error in LLM call or parsing for resource {resource}: {e}") 
        explanation = f"The resource {resource} ({service}) shows potential for optimization. The suggestion is to '{suggestion}' based on its usage metrics (e.g., CPU: {cpu:.1f}%, Mem: {mem:.1f}%) and cost of ${cost:.2f}."
        action_plan = f"**Suggestion:** {suggestion}\n\n*Action: Please review this resource manually. The automated step-by-step generation failed. Based on the suggestion, you should investigate rightsizing the instance or changing its storage class.*"
        return explanation, action_plan