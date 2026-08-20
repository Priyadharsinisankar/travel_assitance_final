import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

MODEL = "gemini-3.7-flash"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_FILE = os.path.join(BASE_DIR, "knowledge_base.json")


def load_knowledge():
    try:
        with open(KB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Knowledge base error:", e)
        return {}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Invalid request."
            }), 400

        message = data.get("message", "").strip()

        history = data.get("history", [])

        if not message:
            return jsonify({
                "error": "Message is empty."
            }), 400

        # Check API key
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            return jsonify({
                "error": "GEMINI_API_KEY is not configured."
            }), 500

        # Load local knowledge
        knowledge = load_knowledge()

        # Convert knowledge to text
        knowledge_text = json.dumps(
            knowledge,
            indent=2,
            ensure_ascii=False
        )

        # Conversation history
        history_text = ""

        for item in history[-20:]:

            role = item.get("role", "")
            content = item.get("content", "")

            history_text += (
                f"{role.upper()}: {content}\n"
            )

        prompt = f"""
You are Travel Assistance, a domain-specific travel chatbot.

SUPPORTED TOPICS:

1. Packing checklist
2. Station facilities
3. Simulated train/PNR status
4. Student travel assistance

IMPORTANT RULES:

- Use the local knowledge base as the primary source.
- Never invent station-specific information.
- Never invent train-specific information.
- If information is not available, clearly say that it is unavailable.
- Train and PNR information is SIMULATED only.
- Never claim that simulated information is live.
- Understand follow-up questions using conversation history.
- For packing questions, consider journey duration and season.
- Be helpful and concise.
- If the question is unrelated to travel assistance, politely redirect the user.

LOCAL KNOWLEDGE BASE:

{knowledge_text}

CONVERSATION HISTORY:

{history_text}

CURRENT USER MESSAGE:

{message}

Answer the user now.
"""

        print("\nUser:", message)
        print("Calling Gemini...")

        client = genai.Client(
            api_key=api_key
        )

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        reply = response.text

        print("Gemini response received.")

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        print("\n========== GEMINI ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("==================================\n")

        return jsonify({
            "error": f"Gemini error: {str(e)}"
        }), 500


if __name__ == "__main__":

    print("--------------------------------")
    print("Travel Assistance Chatbot")
    print("--------------------------------")
    print("Model:", MODEL)
    print(
        "API Key:",
        "SET" if os.environ.get("GEMINI_API_KEY") else "NOT SET"
    )
    print("Starting Flask server...")
    print("http://127.0.0.1:5000")
    print("--------------------------------")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )