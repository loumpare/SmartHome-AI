import os
import uvicorn # pyright: ignore[reportMissingImports]
import asyncio
import json
from typing import List
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks # pyright: ignore[reportMissingImports]
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from fastapi.middleware.cors import CORSMiddleware # pyright: ignore[reportMissingImports]

# Local imports
from .Tools import (
    control_lights, 
    get_weather_forecast, 
    get_daily_calendar, 
    summarize_recent_emails,
    compile_news_reports
)  
from .Agents import SmartAgent # pyright: ignore[reportMissingImports]

app = FastAPI(title="AI Home Assistant API")

# Variable globale pour stocker l'action en attente de validation
pending_action = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class UserRequest(BaseModel):
    instruction: str

# --- LLM CONFIGURATION ---
llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio", 
    model="ministral-3-3b",
    temperature=0
)

# --- AGENT ORCHESTRATION ---
router_agent = SmartAgent(
    llm, 
    "Router", 
    "You are a professional dispatcher. Categorize the user's request. "
    "If the user asks for NEWS, REPORTS, EMAILS or CALENDAR, you MUST respond with 'PERSONAL_AGENT'. "
    "If the user asks for climate, weather, or temperature, you MUST respond with 'WEATHER_AGENT'. "
    "If the user asks for lights, home appliances, you MUST respond with 'DOMO_AGENT'. "
    "Otherwise, respond with 'GENERAL'. Do not explain. Just one word."
)

domo_agent = SmartAgent(
    llm, 
    "HomeAutomation", 
    "You are a home automation expert. Use the 'control_lights' tool for any light requests.", 
    tools=[control_lights]
)

weather_agent = SmartAgent(
    llm, 
    "WeatherExpert", 
    "Expert in weather. You MUST use 'get_weather_forecast' and provide the 'location' argument if mentioned.", 
    tools=[get_weather_forecast]
)

news_agent = SmartAgent(
    llm, 
    "NewsAnalyst", 
    "Expert in news aggregation.",
    tools=[get_daily_calendar, summarize_recent_emails, compile_news_reports]
)

# --- API ROUTES ---

@app.post("/ask-agent")
async def ask_agent(request: UserRequest):
    global pending_action
    execution_details = []
    
    # Étape 1 : Routage
    routing_decision = router_agent.invoke(request.instruction).content.upper().strip()

    # Étape 2 : Sélection de l'agent
    if "WEATHER_AGENT" in routing_decision:
        active_agent = weather_agent
    elif "DOMO_AGENT" in routing_decision:
        active_agent = domo_agent
    elif "PERSONAL_AGENT" in routing_decision:
        active_agent = news_agent
    else:
        response = llm.invoke(request.instruction)
        return {"response": response.content, "details": ["General processing"]}

    # Étape 3 : Invocation de l'agent
    agent_response = active_agent.invoke(request.instruction)
    
    # Étape 4 : Gestion des outils
    if agent_response.tool_calls:
        for tool_call in agent_response.tool_calls:
            tool_name = tool_call["name"]
            
            # --- INTERCEPTION SÉCURITÉ : DOMOTIQUE ---
            if tool_name == "control_lights":
                pending_action = {
                    "tool": "control_lights",
                    "args": tool_call["args"]
                }
                return {
                    "response": f"J'ai préparé une commande pour vos lumières : {tool_call['args']}. Veuillez confirmer.",
                    "needs_validation": True,
                    "action_details": tool_call["args"],
                    "details": ["Waiting for human validation"]
                }
            
            # --- LOGIQUE MÉTÉO (CORRIGÉE) ---
            elif tool_name == "get_weather_forecast":
                # Extraction de la localisation depuis les arguments de l'IA
                location_arg = tool_call.get("args", {}).get("location")
                
                # Appel de l'outil avec l'argument dynamique
                data = get_weather_forecast.invoke({"location": location_arg})
                
                final = llm.invoke(f"Weather Data: {data}. Answer the user: {request.instruction}")
                return {"response": final.content, "details": [f"Weather checked for {location_arg or 'Home'}"]}
            
            # --- LOGIQUE CALENDRIER / MAILS ---
            elif tool_name in ["get_daily_calendar", "summarize_recent_emails"]:
                data = get_daily_calendar.invoke({}) if "calendar" in tool_name else summarize_recent_emails.invoke({})
                final = llm.invoke(f"Personal Data: {data}. Summarize this for the user.")
                return {"response": final.content, "details": [f"Source: {tool_name}"]}
            
            # --- LOGIQUE NEWS ---
            elif tool_name == "compile_news_reports":
                raw_news = compile_news_reports.invoke(tool_call["args"])
                today = datetime.now().strftime('%Y-%m-%d')
                news_prompt = f"CONTEXT: Today is {today}.\nRAW RSS DATA:\n{raw_news}\n\nSummarize correctly."
                final_news = llm.invoke(news_prompt)
                return {"response": final_news.content, "details": ["News review completed"]}
        
        return {"response": "Tâches terminées.", "details": execution_details}
    
    return {"response": agent_response.content, "details": [f"Handled by {active_agent.name}"]}

# NOUVELLE ROUTE : Confirmation de l'action en attente
@app.post("/confirm-action")
async def confirm_action():
    global pending_action
    if not pending_action:
        return {"response": "Aucune action en attente.", "success": False}
    
    try:
        if pending_action["tool"] == "control_lights":
            res = control_lights.invoke(pending_action["args"])
            pending_action = {} # Reset
            return {"response": f"Action exécutée : {res}", "success": True}
    except Exception as e:
        return {"response": f"Erreur : {str(e)}", "success": False}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)