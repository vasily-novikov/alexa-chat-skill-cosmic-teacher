import os
import re
import json
import requests
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# === Configuration ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"
VOICE_NAME = "Hans"  # Alexa voice for responses

# ~500 tokens = ~1500 characters. Keep total request small and cheap.
MAX_INPUT_CHARS = 1500

# === Utility helpers ===
def with_voice(text):
    """Wrap text with SSML prosody tag for deeper voice."""
    return f'<voice name="Hans"><prosody pitch="x-low">{text}</prosody></voice>'
def trim_text(text, limit=MAX_INPUT_CHARS):
    """Trim text to a safe length without cutting words mid-way."""
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."

# === Core OpenAI call ===
def call_openai(prompt: str, context: str = "") -> tuple[str, int]:
    """Send prompt to OpenAI and return reply + total token estimate."""
    prompt = trim_text(prompt)
    context = trim_text(context)

    # --- Short, motivational system prompt ---
    system_message = (
        "You are Yoda, a friendly chat partner for a 13-year-old boy. "
        "Keep replies short, natural, and positive. "
        "Encourage him to talk more and ask brief follow-up questions. "
        "Sound warm and curious, not like a teacher."
    )
    
    user_message = f"Chat so far: {context}\nBoy says: {prompt}" if context else prompt

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 80,  # short spoken replies (~40 words)
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        res = requests.post(OPENAI_URL, headers=headers, json=data, timeout=20)
        res.raise_for_status()
        j = res.json()
    except Exception as e:
        print("OpenAI API error:", e)
        return "Sorry, I couldn't reach the AI service right now.", 0

    # --- Extract text safely ---
    reply = ""
    total_tokens = 0
    try:
        if "choices" in j and len(j["choices"]) > 0:
            reply = j["choices"][0]["message"]["content"].strip()
        if "usage" in j and "total_tokens" in j["usage"]:
            total_tokens = j["usage"]["total_tokens"]
        reply = reply or "Hmm, I'm not sure what to say right now."
    except Exception as e:
        print("Parse error:", e)
        reply = "Sorry, something went wrong with the reply."

    return reply, total_tokens

# === Alexa Handlers ===
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return handler_input.request_envelope.request.object_type == "LaunchRequest"

    def handle(self, handler_input):
        speak = with_voice("Grüße dich! Yoda ich bin, dein Chat-Kumpel. Erzählen mir, du willst?")
        reprompt = with_voice("Erzählen mir etwas, du kannst. Worüber reden möchtest du?")
        print(f"Launch: speak={speak}")
        print(f"Launch: reprompt={reprompt}")
        response = handler_input.response_builder.speak(speak).ask(reprompt).response
        print(f"Launch response: {response}")
        return response


class ChatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name == "ChatIntent"

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        user_text = slots["utterance"].value if "utterance" in slots and slots["utterance"].value else ""
        if not user_text:
            msg = with_voice("Verstanden, ich habe nicht. Wiederholen, du kannst?")
            return handler_input.response_builder.speak(msg).ask(msg).response

        # Load short context
        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        context = " ".join(history[-3:])  # last 3 turns for continuity

        ai_reply, token_count = call_openai(user_text, context)

        # Save for next turn
        history.append(f"User: {user_text}")
        history.append(f"AI: {ai_reply}")
        session["conversation_history"] = history[-6:]
        handler_input.attributes_manager.session_attributes = session

        return handler_input.response_builder.speak(
            with_voice(ai_reply)
        ).ask(with_voice("Weiter reden, du möchtest?")).response


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name == "AMAZON.HelpIntent"

    def handle(self, handler_input):
        speak = with_voice("Über alles reden, mit mir du kannst — Spiele, Schule, Ideen. Hmm!")
        return handler_input.response_builder.speak(speak).ask(speak).response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.FallbackIntent - treats unrecognized utterances as chat."""
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name == "AMAZON.FallbackIntent"

    def handle(self, handler_input):
        # Get the raw text from the request
        req = handler_input.request_envelope.request
        # For FallbackIntent, we need to get the original utterance differently
        # Try to get it from the intent's slots or use a generic response
        user_text = "Hallo"  # Default if we can't get the utterance
        
        # Actually process as a chat message if possible
        session = handler_input.attributes_manager.session_attributes
        history = session.get("conversation_history", [])
        context = " ".join(history[-3:])
        
        ai_reply, token_count = call_openai(user_text, context)
        
        history.append(f"User: {user_text}")
        history.append(f"AI: {ai_reply}")
        session["conversation_history"] = history[-6:]
        handler_input.attributes_manager.session_attributes = session
        
        return handler_input.response_builder.speak(
            with_voice(ai_reply)
        ).ask(with_voice("Weiter reden, du möchtest?")).response


class CancelOrStopHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name in [
            "AMAZON.CancelIntent",
            "AMAZON.StopIntent",
        ]

    def handle(self, handler_input):
        return handler_input.response_builder.speak(
            with_voice("Gehen du musst. Auf Wiedersehen, junger Padawan!")
        ).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return handler_input.request_envelope.request.object_type == "SessionEndedRequest"

    def handle(self, handler_input):
        # Clean up session data if needed
        return handler_input.response_builder.response


# === Skill Builder ===
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ChatIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(CancelOrStopHandler())
sb.add_request_handler(SessionEndedRequestHandler())

lambda_handler = sb.lambda_handler()
handler = lambda_handler  # Alias for Alexa-hosted skills

