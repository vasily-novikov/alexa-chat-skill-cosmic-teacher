import os
import re
import json
import requests
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

# === Configuration ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"
MAX_INPUT_CHARS = 1500

# === Utility helpers ===
def trim_text(text, limit=MAX_INPUT_CHARS):
    """Trim text to a safe length without cutting words mid-way."""
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."

# === Core OpenAI call ===
def call_openai(prompt: str, context: str = ""):
    """Send prompt to OpenAI and return reply + total token estimate."""
    prompt = trim_text(prompt)
    context = trim_text(context)

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
        "max_tokens": 80,
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
        speak = "Hallo! Yoda ich bin, dein Chat-Kumpel. Worüber möchtest du sprechen?"
        return (
            handler_input.response_builder
            .speak(speak)
            .ask(speak)
            .response
        )

class ChatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name == "ChatIntent"

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        user_text = slots.get("utterance").value if slots.get("utterance") else ""
        
        if not user_text:
            speak = "Hmm, nichts gehört habe ich. Noch einmal versuchen kannst du?"
            return handler_input.response_builder.speak(speak).ask(speak).response
        
        session_attr = handler_input.attributes_manager.session_attributes
        context = session_attr.get("context", "")
        
        reply, tokens = call_openai(user_text, context)
        
        new_context = f"{context}\nUser: {user_text}\nYoda: {reply}"
        session_attr["context"] = trim_text(new_context, limit=500)
        
        return (
            handler_input.response_builder
            .speak(reply)
            .ask("Was noch sagen möchtest du?")
            .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return req.object_type == "IntentRequest" and req.intent.name == "AMAZON.HelpIntent"

    def handle(self, handler_input):
        speak = "Ich bin Yoda, dein Chat-Partner. Einfach erzähle mir, was du möchtest!"
        return handler_input.response_builder.speak(speak).ask(speak).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        req = handler_input.request_envelope.request
        return (req.object_type == "IntentRequest" and 
                req.intent.name in ["AMAZON.CancelIntent", "AMAZON.StopIntent"])

    def handle(self, handler_input):
        speak = "Auf Wiedersehen! Bald sprechen wir wieder."
        return handler_input.response_builder.speak(speak).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return handler_input.request_envelope.request.object_type == "SessionEndedRequest"

    def handle(self, handler_input):
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        print(f"Exception: {exception}")
        speak = "Entschuldigung, ein Fehler ist aufgetreten. Bitte versuche es noch einmal."
        return (
            handler_input.response_builder
            .speak(speak)
            .ask(speak)
            .response
        )

# === Skill Builder ===
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(ChatIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

# Lambda handler entry point
lambda_handler = sb.lambda_handler()
