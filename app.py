import os
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from google import genai
from google.genai import types

from chatbot_config import BOT_NAME, SYSTEM_PROMPT

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
active_chats = {}


def get_chat_session():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]

    if session_id not in active_chats:
        active_chats[session_id] = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )

    return active_chats[session_id]


@app.route("/")
def index():
    return render_template("index.html", bot_name=BOT_NAME)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"reply": "Please type a question to get started."}), 400

    if client is None:
        return jsonify({"reply": "GEMINI_API_KEY is missing in the .env file."}), 500

    try:
        response = get_chat_session().send_message(user_message)
        reply = response.text or "Sorry, I could not generate a response. Please try again."
    except Exception as error:
        reply = f"Something went wrong while contacting the AI service: {error}"

    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    session_id = session.pop("session_id", None)
    if session_id:
        active_chats.pop(session_id, None)
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(debug=True)
