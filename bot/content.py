import json, os, re
from pathlib import Path

FACTS = json.loads((Path(__file__).parents[1] / 'data' / 'facts.json').read_text())

def choose_fact(day):
    import datetime
    idx = (datetime.date.fromisoformat(day) - datetime.date(2026, 1, 1)).days % len(FACTS)
    return FACTS[idx]

def script_for(fact):
    # Factual narration is assembled from reviewed text; no hallucinated assertions.
    return f"Did you know? {fact['fact']} Science is full of surprises. Follow for another amazing fact!"

def optional_ai_rewrite(fact, narration):
    if not os.getenv('GEMINI_API_KEY'):
        return narration
    try:
        from google import genai
        client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        prompt = ("Rewrite this short English narration in a lively style, 35 to 65 words. "
                  "Use ONLY the factual statements given. Do not add new claims, numbers or details. "
                  "Return ONLY narration. Fact: " + fact['fact'])
        response = client.models.generate_content(model=model, contents=prompt)
        text = (response.text or '').strip()
        # For zero-review automated publishing, avoid AI rewriting by default.
        if os.getenv('ALLOW_AI_REWRITE') == '1' and 20 <= len(text.split()) <= 80:
            return text
    except Exception as exc:
        print('AI rewrite unavailable; using reviewed script:', str(exc)[:150])
    return narration

def video_metadata(fact, day):
    marker = f"[science-shorts:{day}:{fact['id']}]"
    return {
        'title': f"{fact['title']} #Shorts"[:100],
        'description': f"{fact['fact']}\n\nSource: {fact['source']}\n\n#Shorts #Science #AmazingFacts\n{marker}",
        'tags': ['science', 'facts', 'amazing facts', 'shorts'],
        'marker': marker,
    }
