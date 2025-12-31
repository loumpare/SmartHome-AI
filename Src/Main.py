import os
import uvicorn # pyright: ignore[reportMissingImports]
import asyncio
from typing import List
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks # pyright: ignore[reportMissingImports]
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

# Local imports from our anonymized files
from .tools import (# pyright: ignore[reportMissingImports]
    control_lights, 
    get_weather_forecast, 
    get_daily_calendar, 
    summarize_recent_emails,
    compile_news_reports
)  
from .agents import SmartAgent # pyright: ignore[reportMissingImports]

app = FastAPI(title="AI Home Assistant API")

# --- DATA MODELS ---
class UserRequest(BaseModel):
    instruction: str

# --- LLM CONFIGURATION ---
# Using environment variables for sensitive URLs
LLM_BASE_URL = os.getenv("LLM_URL", "http://localhost:1234/v1")

llm = ChatOpenAI(
    base_url=LLM_BASE_URL, 
    api_key="internal-key", # Placeholder for local LLM
    model="mistral-7b-instruct", 
    temperature=0
)

# --- AGENT ORCHESTRATION ---

# The Router (Arbitrator) decides which specialized agent should handle the request
router_agent = SmartAgent(
    llm, 
    "Router", 
    "You are a routing assistant. Respond with exactly one word: "
    "'WEATHER_AGENT' for climate/temperature, "
    "'DOMO_AGENT' for lights/home appliances, "
    "'PERSONAL_AGENT' for calendar, emails, or NEWS/REPORTS. "
    "Otherwise, respond with 'GENERAL'."
)

domo_agent = SmartAgent(
    llm, 
    "HomeAutomation", 
    "Expert in smart home control.", 
    tools=[control_lights]
)

weather_agent = SmartAgent(
    llm, 
    "WeatherExpert", 
    "Expert in weather forecasting and local conditions.", 
    tools=[get_weather_forecast]
)

news_agent = SmartAgent(
    llm, 
    "NewsAnalyst", 
    "Expert in news aggregation. When asked for news, always use 'compile_news_reports' "
    "selecting AT LEAST 3 different sources for comparison. Provide a structured synthesis.",
    tools=[get_daily_calendar, summarize_recent_emails, compile_news_reports]
)

# --- API ROUTES ---

@app.post("/ask-agent")
async def ask_agent(request: UserRequest):
    """
    Main endpoint that routes user instructions to the appropriate AI agent.
    """
    execution_details = []
    
    # Step 1: Route the request
    routing_decision = router_agent.invoke(request.instruction).content.upper()

    # Step 2: Select the active agent based on routing
    if "WEATHER_AGENT" in routing_decision:
        active_agent = weather_agent
    elif "DOMO_AGENT" in routing_decision:
        active_agent = domo_agent
    elif "PERSONAL_AGENT" in routing_decision:
        active_agent = news_agent
    else:
        # General conversation fallback
        response = llm.invoke(request.instruction)
        return {"response": response.content, "details": ["General processing"]}

    # Step 3: Execute Agent Logic
    agent_response = active_agent.invoke(request.instruction)
    
    # Step 4: Handle Tool Calls (Functional Execution)
    if agent_response.tool_calls:
        for tool_call in agent_response.tool_calls:
            tool_name = tool_call["name"]
            
            # Weather logic
            if tool_name == "get_weather_forecast":
                data = get_weather_forecast.invoke({})
                final = llm.invoke(f"Weather Data: {data}. Answer the user: {request.instruction}")
                return {"response": final.content, "details": ["Weather service queried"]}
            
            # Lighting logic
            elif tool_name == "control_lights":
                res = control_lights.invoke(tool_call["args"])
                execution_details.append(res)
            
            # Personal data logic (Calendar/Email)
            elif tool_name in ["get_daily_calendar", "summarize_recent_emails"]:
                data = get_daily_calendar.invoke({}) if "calendar" in tool_name else summarize_recent_emails.invoke({})
                final = llm.invoke(f"Personal Data: {data}. Summarize this for the user.")
                return {"response": final.content, "details": [f"Source: {tool_name}"]}
            
            # News logic with specific constraints
            elif tool_name == "compile_news_reports":
                raw_news = compile_news_reports.invoke(tool_call["args"])
                today = datetime.now().strftime('%Y-%m-%d')
                
                news_prompt = (
                    f"CONTEXT: Today is {today}.\n"
                    f"RAW RSS DATA:\n{raw_news}\n\n"
                    "WRITING INSTRUCTIONS:\n"
                    "1. Process at least 3 different sources.\n"
                    "2. Explicitly cite sources (e.g., 'According to Source A...').\n"
                    "3. Highlight differences in perspectives if any.\n"
                    "4. End with a 'Sources Consulted' section.\n"
                    "5. STRICTLY FORBIDDEN: Do not use internal knowledge. Only use the provided RSS lines."
                )
                
                final_news = llm.invoke(news_prompt)
                return {"response": final_news.content, "details": ["Comparative news review completed"]}
        
        return {"response": "Tasks completed successfully.", "details": execution_details}
    
    # Fallback for text-only agent responses
    return {"response": agent_response.content, "details": [f"Handled by {active_agent.name}"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)