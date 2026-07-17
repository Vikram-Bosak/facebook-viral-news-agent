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
1. Understand the main topic and its emotional tone.
2. Choose ONE of the following styles that best fits the news:
   - "Meme Style"
   - "Funny Style"
   - "Emotional Style"
   - "Sad Style"
   - "Breaking News Style"
   - "Celebrity Reaction Style"
   - "Comparison Style"
   - "Storytelling Style"
3. Generate a hyper-engaging, dramatic, and curiosity-inducing 'headline' (MAX 10 WORDS). This will be written directly on the viral image, so it must grab attention instantly (e.g., "THE TRUTH FINALLY COMES OUT!" or "FANS ARE LOSING IT OVER THIS!").
4. Generate a viral 'hook_text' (1-2 sentences) to complement the headline.
5. Highlight 1 to 3 important keywords in the headline by wrapping them in asterisks like *this* to make them stand out in a different color.

Respond STRICTLY in JSON format with three keys: "headline", "hook_text", and "style". Do not include markdown formatting or backticks around the JSON.
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
            "hook_text": "The entire internet is talking about this. What do you think about the latest drama?",
            "style": "Breaking News Style"
        }

def generate_facebook_caption(title):
    logging.info(f"Generating Facebook caption for: {title}")
    prompt = f"""
Write a highly engaging Facebook post caption for an American entertainment news page called 'Celebrity Buzz USA'.
The post is about this news title: {title}

Requirements:
- Keep it catchy, exciting, and short (3-4 sentences max).
- Include 2-3 relevant emojis.
- Include an engaging hook or question at the end to drive comments.
- Include 5-6 relevant hashtags at the very bottom (like #HollywoodNews, #Trending).
- Do not include markdown formatting, just the raw text ready for Facebook.
"""
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            top_p=0.95,
            max_tokens=1024,
            stream=False
        )
        caption = completion.choices[0].message.content.strip()
        if not caption:
            raise Exception("Empty response from LLM")
        return caption
    except Exception as e:
        logging.error(f"LLM caption generation failed: {e}")
        return (
            f"🚨 Hollywood Update! 🚨\n\n"
            f"{title}\n\n"
            f"Stay tuned for more updates! 👇\n"
            f"#HollywoodNews #CelebrityBuzz #Trending #Entertainment #News #CelebrityBuzzUSA"
        )
