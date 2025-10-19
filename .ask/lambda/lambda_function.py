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
        can = handler_input.request_envelope.request.object_type == "LaunchRequest"
        print(f"LaunchRequestHandler.can_handle: {can}")
        return can

    def handle(self, handler_input):
        print("LaunchRequestHandler.handle called")
        locale = handler_input.request_envelope.request.locale
        print(f"Locale: {locale}")
        
        if locale.startswith('de'):
            speak = with_voice("Grüße dich! Yoda ich bin, dein Chat-Kumpel. Erzählen mir, du willst?")
            reprompt = with_voice("Erzählen mir etwas, du kannst. Worüber reden möchtest du?")
        else:
            speak = with_voice("Greetings! Yoda I am, your chat buddy. Tell me something, you will?")
            reprompt = with_voice("Speak to me, you can. What talk about, you wish?")
        
        print(f"Launch: speak={speak}")
        print(f"Launch: reprompt={reprompt}")
        response = handler_input.response_builder.speak(speak).ask(reprompt).response
        print(f"Launch response: {response}")
        return response


class ChatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        can = req.object_type == "IntentRequest" and req.intent.name == "ChatIntent"
        print(f"ChatIntentHandler.can_handle: {can}")
        return can

    def handle(self, handler_input):
        print("ChatIntentHandler.handle called")
        slots = handler_input.request_envelope.request.intent.slots
        user_text = slots["utterance"].value if "utterance" in slots and slots["utterance"].value else ""
        print(f"ChatIntent utterance: {user_text}")
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
        can = req.object_type == "IntentRequest" and req.intent.name == "AMAZON.HelpIntent"
        print(f"HelpIntentHandler.can_handle: {can}")
        return can

    def handle(self, handler_input):
        print("HelpIntentHandler.handle called")
        speak = with_voice("Über alles reden, mit mir du kannst — Spiele, Schule, Ideen. Hmm!")
        return handler_input.response_builder.speak(speak).ask(speak).response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for AMAZON.FallbackIntent - treats unrecognized utterances as chat."""
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        can = req.object_type == "IntentRequest" and req.intent.name == "AMAZON.FallbackIntent"
        print(f"FallbackIntentHandler.can_handle: {can}")
        return can

    def handle(self, handler_input):
        print("FallbackIntentHandler.handle called")
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
        can = req.object_type == "IntentRequest" and req.intent.name in [
            "AMAZON.CancelIntent",
            "AMAZON.StopIntent",
        ]
        print(f"CancelOrStopHandler.can_handle: {can}")
        return can

    def handle(self, handler_input):
        print("CancelOrStopHandler.handle called")
        return handler_input.response_builder.speak(
            with_voice("Gehen du musst. Auf Wiedersehen, junger Padawan!")
        ).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        can = handler_input.request_envelope.request.object_type == "SessionEndedRequest"
        print(f"SessionEndedRequestHandler.can_handle: {can}")
        return can

    def handle(self, handler_input):
        print("SessionEndedRequestHandler.handle called")
        req = handler_input.request_envelope.request
        print(f"Session ended reason: {getattr(req, 'reason', 'UNKNOWN')}")
        print(f"Session ended error: {getattr(req, 'error', 'NONE')}")
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

# Wrapper to log all incoming requests
def logged_handler(event, context):
    """Log all incoming requests before processing."""
    import json
    print("=" * 80)
    print("INCOMING REQUEST:")
    print(f"Request type: {event.get('request', {}).get('type', 'UNKNOWN')}")
    if event.get('request', {}).get('type') == 'IntentRequest':
        print(f"Intent name: {event.get('request', {}).get('intent', {}).get('name', 'UNKNOWN')}")
        print(f"Intent slots: {event.get('request', {}).get('intent', {}).get('slots', {})}")
    print(f"Session new: {event.get('session', {}).get('new', 'UNKNOWN')}")
    print(f"Full request: {json.dumps(event, indent=2, default=str)[:1000]}...")
    print("=" * 80)
    
    # Call the actual handler
    return sb.lambda_handler()(event, context)

lambda_handler = logged_handler
handler = logged_handler  # Alias for Alexa-hosted skills

