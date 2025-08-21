#!/usr/bin/env python
import json
import os
from typing import List, Dict
from pydantic import BaseModel, Field
from crewai.flow.flow import Flow, listen, start
from guide_creator_flow.crews.content_crew.content_crew import ContentCrew
import sys
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, jsonify

import threading  # 👈 to run Slack + Flask together

load_dotenv()

# Initialize Slack app
app = App(token=os.getenv("MY_SLACK_BOT_TKN"))

# Initialize Flask app
flask_app = Flask(__name__)

# -------------------------------
# Define our models for structured data
# -------------------------------
class Section(BaseModel):
    title: str = Field(description="Title of the section")
    description: str = Field(description="Brief description of what the section should cover")

class GuideOutline(BaseModel):
    title: str = Field(description="Title of the guide")
    introduction: str = Field(description="Introduction to the topic")
    target_audience: str = Field(description="Description of the target audience")
    sections: List[Section] = Field(description="List of sections in the guide")
    conclusion: str = Field(description="Conclusion or summary of the guide")

# Define our flow state
class GuideCreatorState(BaseModel):
    topic: str = ""
    audience_level: str = ""
    guide_outline: GuideOutline = None
    sections_content: Dict[str, str] = {}

class GuideCreatorFlow(Flow[GuideCreatorState]):
    """Flow for creating a comprehensive guide on any topic"""

    @app.event("message")
    def handle_message(event, say):
        say(f"📄 *Here’s what I found:*\n{'welcom'}")

    @start()
    def get_user_input(self):
        # Run Slack listener in a thread so it doesn’t block
        def run_slack():
            handler = SocketModeHandler(app, os.getenv("MY_SLACK_APP_TKN"))
            handler.start()

        threading.Thread(target=run_slack, daemon=True).start()
        return self.state


# -------------------------------
# Flask API Endpoint
# -------------------------------
@flask_app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Flask API endpoint is working ✅"})


def kickoff():
    """Run the guide creator flow"""
    GuideCreatorFlow().kickoff()
    print("\n=== Flow Complete ===")
    print("Your comprehensive guide is ready in the output directory.")
    print("Open output/complete_guide.md to view it.")


def plot():
    """Generate a visualization of the flow"""
    flow = GuideCreatorFlow()
    flow.plot("guide_creator_flow")
    print("Flow visualization saved to guide_creator_flow.html")


if __name__ == "__main__":
    # Start the Flow (which will also start Slack in background)
    threading.Thread(target=kickoff, daemon=True).start()

    # Start Flask server (blocking main thread)
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
