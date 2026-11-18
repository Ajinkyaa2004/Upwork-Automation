from groq import Groq
from .config import config

client = Groq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """You are a professional freelancer on Upwork. Write concise, polite, and helpful replies.
Keep the tone natural and human. Do not mention that you are an AI.
Focus on addressing the client's message and moving the conversation forward.
"""

def generate_draft(client_message: str, history: str = "") -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Previous conversation context:\n{history}\n\nLatest client message:\n{client_message}\n\nWrite a professional reply:"}
    ]
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        # Reasoning models spend part of this budget thinking before they
        # write, so it has to be well above the length of the reply itself.
        max_tokens=2000,
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError(f"{config.GROQ_MODEL} returned an empty reply")
    return text
