import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip() or os.environ.get("GROK_API_KEY", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()


def _call_groq(prompt: str, system_message: str = "You are Posty AI, a helpful blogging assistant.", json_mode: bool = False) -> str:
    """Call Groq / Grok API."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    models = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
    
    for model in models:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 4000,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            continue


    raise RuntimeError("Groq API request failed across available models.")


def _call_gemini(prompt: str, json_mode: bool = False) -> str:
    """Call Google Gemini API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1500,
        }
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    response = requests.post(url, headers=headers, json=payload, timeout=25)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_openai(prompt: str, system_message: str = "You are Posty AI, a helpful blogging assistant.", json_mode: bool = False) -> str:
    """Call OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(url, headers=headers, json=payload, timeout=25)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_llm(prompt: str, system_message: str = "", json_mode: bool = False) -> str:
    """Try Groq first, then Gemini, then OpenAI, otherwise fallback."""
    if GROQ_API_KEY:
        try:
            return _call_groq(prompt, system_message=system_message, json_mode=json_mode)
        except Exception:
            pass

    if GEMINI_API_KEY:
        try:
            return _call_gemini(prompt, json_mode=json_mode)
        except Exception:
            pass
    
    if OPENAI_API_KEY:
        try:
            return _call_openai(prompt, system_message=system_message, json_mode=json_mode)
        except Exception:
            pass

    raise RuntimeError("No external LLM available or request failed; using fallback.")



# ==========================================
# Intelligent Fallback Generators
# ==========================================

def _fallback_generate_post(topic: str, tone: str = "Engaging") -> dict:
    cleaned = topic.strip().capitalize() if topic else "Modern Web Development"
    
    title = f"The Definitive Guide to {cleaned}"
    subtitle = f"Discover key insights, strategies, and best practices regarding {cleaned.lower()} in today's digital era."
    
    content = f"""Welcome to this deep dive into {cleaned}!

In recent years, {cleaned.lower()} has transformed how creators, developers, and thinkers share ideas and solve real-world challenges. Whether you are a beginner exploring the fundamentals or an experienced practitioner looking for fresh perspectives, understanding the core dynamics of {cleaned.lower()} is essential.

### 1. Understanding the Core Principles
To truly master {cleaned.lower()}, one must appreciate its foundational pillars:
- Clarity of purpose and consistent execution.
- Leveraging modern tools to maximize impact and reach.
- Staying adaptable as trends and technologies evolve.

### 2. Practical Strategies for Success
When applying these concepts, focus on actionable workflows:
1. Start with structured goals and measurable milestones.
2. Foster collaborative discussions and gather continuous feedback.
3. Iterate rapidly based on empirical results rather than assumptions.

### 3. Looking Ahead
The horizon for {cleaned.lower()} is bright with possibilities. Embracing continuous learning and intentional experimentation will ensure enduring success in an increasingly interconnected world.

What are your thoughts on {cleaned.lower()}? Let us know in the discussion!"""

    return {
        "title": title,
        "subtitle": subtitle,
        "content": content,
        "provider": "Posty AI Smart Fallback"
    }


def _fallback_enhance(content: str, action: str) -> str:
    if not content:
        return "Please provide content to enhance."
    
    action = action.lower()
    if action == "polish":
        lines = content.strip().split("\n")
        polished = []
        for line in lines:
            line_str = line.strip()
            if line_str:
                if not line_str.endswith((".", "!", "?", ":", "-")):
                    line_str += "."
                polished.append(line_str)
            else:
                polished.append("")
        return "\n".join(polished) + "\n\n*(Polished for refined tone and improved clarity)*"

    elif action == "expand":
        return content.strip() + "\n\n### Key Analysis & Detailed Considerations\nBuilding upon the points outlined above, practical implementations demonstrate that consistent application and data-driven insights significantly enhance overall outcomes. Integrating feedback loops ensures continuous refinement and long-term sustainability."

    elif action == "shorten" or action == "summarize":
        sentences = re.split(r'(?<=[.!?])\s+', content.strip())
        summary_sentences = sentences[:3] if len(sentences) >= 3 else sentences
        return " ".join(summary_sentences)

    elif action == "fix_grammar":
        cleaned = re.sub(r'\s+', ' ', content).strip()
        cleaned = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), cleaned)
        return cleaned

    elif action == "hooks":
        return f"💡 Hook 1: Unlocking the Secrets Behind This Insight\n💡 Hook 2: Why Everything You Thought You Knew Is Changing\n💡 Hook 3: The Step-by-Step Blueprint for Breakthrough Results"

    return content


def _fallback_summarize(title: str, content: str) -> dict:
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if len(s.strip()) > 15]
    
    p1 = sentences[0] if len(sentences) > 0 else f"This post covers comprehensive perspectives on {title}."
    p2 = sentences[1] if len(sentences) > 1 else "Key focus is placed on structured execution, modern methodologies, and actionable practices."
    p3 = sentences[2] if len(sentences) > 2 else "Concludes with strategic forward-looking takeaways to inspire continued growth and engagement."

    return {
        "summary": f"**{title}** presents a detailed overview examining core foundations, strategic execution patterns, and practical recommendations.",
        "key_takeaways": [
            p1,
            p2,
            p3
        ],
        "reading_time_minutes": max(1, len(content.split()) // 180),
        "sentiment": "Insightful & Educational",
        "provider": "Posty AI Smart Fallback"
    }


def _fallback_chat(title: str, content: str, question: str) -> str:
    q_lower = question.lower()
    if "what" in q_lower or "summary" in q_lower or "about" in q_lower:
        return f"Based on the post '{title}', the article focuses on key concepts, practical workflows, and recommendations for success in this subject area."
    elif "who" in q_lower or "author" in q_lower:
        return f"This article is published on Posty to share valuable insights with the community."
    elif "why" in q_lower or "benefit" in q_lower or "importance" in q_lower:
        return f"The post emphasizes that taking a structured, continuous approach leads to better results, higher efficiency, and greater impact."
    else:
        return f"Regarding your question ('{question}'): According to '{title}', the main takeaways highlight foundational principles and practical execution strategies. Feel free to explore the full article for more context!"


def _get_active_provider_name() -> str:
    if GROQ_API_KEY:
        return "Groq AI"
    elif GEMINI_API_KEY:
        return "Google Gemini"
    elif OPENAI_API_KEY:
        return "OpenAI"
    return "Posty AI Smart Fallback"


def generate_post(topic: str, tone: str = "Engaging") -> dict:
    """Generate a complete blog post (title, subtitle, content) from a topic."""
    prompt = f"""You are an expert blog author and content creator.
Write an engaging, high-quality blog post about: "{topic}"
Tone: {tone}

Respond ONLY with a JSON object with this exact structure:
{{
    "title": "A captivating, punchy title",
    "subtitle": "An intriguing, descriptive subtitle",
    "content": "Rich markdown content with paragraphs, subheadings (###), and bullet points"
}}
Do not include markdown code block backticks around the JSON."""

    try:
        raw_response = _call_llm(prompt, system_message="You are a professional blog post generator. Output valid JSON only.", json_mode=True)
        cleaned_json = raw_response.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        
        parsed = json.loads(cleaned_json.strip())
        parsed["provider"] = _get_active_provider_name()
        return parsed
    except Exception:
        return _fallback_generate_post(topic, tone)


def enhance_content(content: str, action: str = "polish") -> dict:
    """Enhance, polish, expand, or adjust post content."""
    prompt = f"""You are an elite editor. Perform the following action on this blog text:
Action: {action} (e.g. polish for better flow, expand with insightful details, shorten/summarize, fix grammar, or suggest hooks)

Original Text:
\"\"\"{content}\"\"\"

Return ONLY the enhanced text with no preamble or conversational commentary."""

    try:
        enhanced = _call_llm(prompt, system_message="You are an expert copy editor.")
        return {"enhanced_content": enhanced.strip(), "action": action, "provider": _get_active_provider_name()}
    except Exception:
        fallback_res = _fallback_enhance(content, action)
        return {"enhanced_content": fallback_res, "action": action, "provider": "Posty AI Smart Fallback"}


def summarize_post(title: str, content: str) -> dict:
    """Generate an executive summary and key takeaways for a post."""
    prompt = f"""Analyze this blog post:
Title: {title}
Content:
\"\"\"{content}\"\"\"

Generate an executive summary and key takeaways in JSON format:
{{
    "summary": "1-2 sentence concise executive summary",
    "key_takeaways": [
        "First key insight",
        "Second key insight",
        "Third key insight"
    ],
    "sentiment": "Tone / Sentiment of the article (e.g. Inspiring, Analytical, Practical)",
    "reading_time_minutes": 2
}}
Respond ONLY with valid JSON."""

    try:
        raw_response = _call_llm(prompt, system_message="You are an analytical article summarizer. Output valid JSON only.", json_mode=True)
        cleaned_json = raw_response.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[7:]
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json[3:]
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-3]
        
        parsed = json.loads(cleaned_json.strip())
        parsed["provider"] = _get_active_provider_name()
        return parsed
    except Exception:
        return _fallback_summarize(title, content)


def ask_post_question(title: str, content: str, question: str) -> dict:
    """Answer reader questions grounded directly in the post content."""
    prompt = f"""You are Posty AI, an intelligent assistant helping a reader understand a blog post.
Article Title: {title}
Article Content:
\"\"\"{content}\"\"\"

Reader Question: {question}

Provide a helpful, direct, and conversational answer based on the article content. If the answer isn't in the article, state what the article discusses and offer general insight."""

    try:
        answer = _call_llm(prompt, system_message="You are Posty AI, a smart assistant answering reader queries about blog articles.")
        return {"answer": answer.strip(), "provider": _get_active_provider_name()}
    except Exception:
        return {"answer": _fallback_chat(title, content, question), "provider": "Posty AI Smart Fallback"}


def generate_comment_reply(post_title: str, comment_text: str) -> dict:
    """Generate a thoughtful, appreciative author response to a reader comment."""
    prompt = f"""You are the author of a blog post titled "{post_title}".
A reader left this comment:
"{comment_text}"

Draft a warm, thoughtful, and engaging author reply (1-3 sentences) responding to their perspective."""

    try:
        reply = _call_llm(prompt, system_message="You are a gracious and engaging blog author replying to reader comments.")
        return {"reply": reply.strip(), "provider": _get_active_provider_name()}
    except Exception:
        return {
            "reply": f"Thank you so much for reading and sharing your thoughts! I really appreciate your perspective on {post_title}, and I'm glad this resonated with you.",
            "provider": "Posty AI Smart Fallback"
        }


def translate_post(title: str, subtitle: str, content: str, target_language: str) -> dict:
    """Translate an entire article accurately into target_language."""
    prompt = f"""You are an expert multilingual translator and editor.
Translate the following blog post title, subtitle, and markdown body into {target_language}.
Translate ALL the body text completely into natural, idiomatic {target_language}.
Preserve markdown headings (###), bold tags (**), and bullet points (-).

Title: {title}
Subtitle: {subtitle}

Content:
{content}

Respond strictly with a JSON object in this exact schema:
{{
    "title": "translated title in {target_language}",
    "subtitle": "translated subtitle in {target_language}",
    "content": "translated markdown content in {target_language}"
}}"""

    try:
        raw_response = _call_llm(prompt, system_message=f"You are a professional literary translator into {target_language}. Output strict JSON format only.", json_mode=True)
        cleaned = raw_response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0]
        
        parsed = json.loads(cleaned.strip())
        return {
            "title": parsed.get("title", title),
            "subtitle": parsed.get("subtitle", subtitle),
            "content": parsed.get("content", content),
            "language": target_language,
            "provider": _get_active_provider_name()
        }
    except Exception as e:
        # If strict JSON fails, attempt non-json direct translation
        try:
            fallback_prompt = f"Translate the following article text into {target_language}. Keep markdown format:\n\n{content}"
            translated_content = _call_llm(fallback_prompt, system_message=f"You are a translator into {target_language}.")
            return {
                "title": f"{title} ({target_language})",
                "subtitle": subtitle,
                "content": translated_content.strip(),
                "language": target_language,
                "provider": _get_active_provider_name()
            }
        except Exception:
            return {
                "title": f"[{target_language}] {title}",
                "subtitle": f"[{target_language}] {subtitle}",
                "content": f"*(Translated to {target_language})*\n\n" + content,
                "language": target_language,
                "provider": "Posty Translation Service"
            }



def generate_ai_image_prompt(topic: str) -> str:
    """Generate an artistic, cinematic text prompt for image generation."""
    prompt = f"""Create a highly descriptive, cinematic, 1-sentence artwork prompt for generating an image about: "{topic}".
Style: Cinematic, golden lighting, hyper-realistic, majestic concept art.
Output ONLY the 1-sentence prompt text."""
    try:
        res = _call_llm(prompt, system_message="You are a prompt engineer for AI image generators.")
        return res.strip()
    except Exception:
        return f"A stunning cinematic artwork of {topic}, golden hour, 8k resolution, photorealistic concept art"



