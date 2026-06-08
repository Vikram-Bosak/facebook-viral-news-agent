import json
import logging
import os
from openai import OpenAI

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY", "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")
)

def generate_content_from_article(title, description):
    logging.info(f"Generating content for article: {title}")
    prompt = f"""
Analyze the following CNN Entertainment news article:
Title: {title}
Description: {description}

Your task:
1. Understand the main topic.
2. Extract the most important information.
3. Generate a click-worthy 'headline' for a Facebook Audience (American English).
4. Generate a viral 'hook_text'.
5. Highlight 1 to 3 important keywords in both headline and hook_text by wrapping them in asterisks like *this*.

Respond STRICTLY in JSON format with two keys: "headline" and "hook_text". Do not include markdown formatting or backticks around the JSON.
"""
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
            stream=True
        )
        
        response_text = ""
        for chunk in completion:
            if not chunk.choices:
                continue
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content
                
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        return json.loads(response_text.strip())
    except Exception as e:
        logging.error(f"LLM API failed: {e}")
        return {
            "headline": f"Shocking Update on *{title}*!",
            "hook_text": "The entire internet is talking about this. What do you think about the latest drama?"
        }
