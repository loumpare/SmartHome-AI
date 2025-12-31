🤖 AI Home OS: Multi-Agent Smart Home Assistant
A modular, privacy-focused Smart Home Assistant powered by Large Language Models (LLM). This project uses a Multi-Agent architecture to route user requests between specialized agents (Weather, News, Personal Agenda, and Home Automation).

🌟 Key Features
Intelligent Routing: A "Router" agent analyzes your request and sends it to the most qualified specialist.

Comparative News Review: Aggregates multiple RSS feeds (Politics, International, Institutional) to provide a balanced overview.

Google Integration: Direct access to your Google Calendar and Gmail (Read-only) via official APIs.

Smart Lighting: Controls Philips Hue systems (via phue library).

Docker Ready: Fully containerized for easy deployment on a home server or Raspberry Pi.

🏗️ Project Structure
Plaintext

├── app/
│   ├── main.py          # FastAPI application & Agent routing
│   ├── tools.py         # Hardware & API tools (News, Google, Weather)
│   ├── agents.py        # SmartAgent class definition
│   └── domotics.py      # Hardware bridge configuration (e.g., Philips Hue)
├── dashboard.py         # Streamlit User Interface
├── Dockerfile           # Backend container config
├── requirements.txt     # Python dependencies
└── .env.example         # Template for environment variables
🚀 Quick Start
1. Prerequisites
Docker & Docker Compose installed.

A running LLM Server (like LM Studio, Ollama, or LocalAI) compatible with the OpenAI API format.

2. Setup Environment Variables
Create a .env file in the root directory:

Extrait de code

# LLM Configuration
LLM_URL=http://your-server-ip:1234/v1

# Smart Home Configuration
HUE_BRIDGE_IP=192.168.1.XX
HOME_LAT=48.85
HOME_LON=2.29

# UI Configuration
BACKEND_API_URL=http://backend:8000/ask-agent
3. Google API Setup (Optional)
To use Calendar and Gmail features:

Go to Google Cloud Console.

Create a project and enable Gmail API and Google Calendar API.

Create OAuth 2.0 Credentials and download the credentials.json file to the project root.

On first run, a token.json will be generated after you authorize the app in your browser.

4. Run with Docker
Bash

docker build -t smarthome-backend .
docker run -p 8000:8000 --env-file .env smarthome-backend
🛠️ Customization
Adding News Sources
You can modify the NEWS_FEEDS dictionary in app/tools.py to add your favorite RSS feeds.

Modifying Agent Behavior
The system prompts for each agent (Router, Analyst, etc.) are located in app/main.py. You can tweak these to change the personality or strictness of the assistant.

🛡️ Privacy & Security
Anonymization: This repository contains no hardcoded IP addresses or API keys. All sensitive data is handled via .env files.

Local First: Designed to run with local LLMs to ensure your requests and personal data (emails, schedule) never leave your network.

📄 License
This project is open-source. Feel free to fork and adapt it to your own smart home setup!
