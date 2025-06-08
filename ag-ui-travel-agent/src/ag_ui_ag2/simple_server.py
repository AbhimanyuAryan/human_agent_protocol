import os
import asyncio
import json
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from autogen import ConversableAgent, LLMConfig, register_function
from src.ag_ui_ag2.database import MEMBER_DATABASE
from src.ag_ui_ag2.messages import SYSTEM_MESSAGE, INITIAL_MESSAGE

load_dotenv()

# Configure LLM
llm_config = LLMConfig(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
)

class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversations: Dict[str, list] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.conversations[client_id] = []
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.conversations:
            del self.conversations[client_id]
            
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

manager = ConnectionManager()

# Travel agent functions (keep same as original)
def lookup_member(member_id: str) -> dict[str, Any]:
    """Look up member details from the database"""
    if member_id in MEMBER_DATABASE:
        return {
            "found": True,
            "name": MEMBER_DATABASE[member_id]["name"],
            "membership": MEMBER_DATABASE[member_id]["membership"],
            "preferences": MEMBER_DATABASE[member_id]["preferences"]
        }
    else:
        return {
            "found": False,
            "message": "Member ID not found in our system"
        }

def create_itinerary(
    destination: str,
    days: int,
    membership_type: str,
    preferences: list
) -> dict[str, Any]:
    """Create a realistic, personalized travel itinerary"""
    if not destination or days <= 0:
        return {"error": "Invalid destination or number of days."}

    itinerary = []
    for day in range(1, days + 1):
        day_plan = {
            "day": f"Day {day}",
            "morning": "",
            "afternoon": "",
            "evening": "",
        }

        if membership_type == "premium":
            day_plan["morning"] = f"Private tour or exclusive experience aligned with: {', '.join(preferences)}"
            day_plan["afternoon"] = "Relax at a luxury spa, explore high-end shopping districts, or enjoy curated local experiences."
            day_plan["evening"] = "Dine at a top-rated restaurant with a reservation made just for you."
        else:
            day_plan["morning"] = f"Join a small group tour covering key attractions related to: {', '.join(preferences)}"
            day_plan["afternoon"] = "Take a self-guided walk or visit a popular local spot recommended by travel experts."
            day_plan["evening"] = "Enjoy a casual dinner at a popular neighborhood restaurant."

        itinerary.append(day_plan)

    return {
        "destination": destination,
        "days": days,
        "itinerary": itinerary,
        "accommodation": "5-star hotel" if membership_type == "premium" else "3-star or boutique hotel",
        "transportation": "Private car service" if membership_type == "premium" else "Local transport and shared rides",
        "is_draft": True
    }

class SimpleUI:
    def __init__(self, client_id: str):
        self.client_id = client_id
        
    async def send_message(self, role: str, content: str):
        message = {
            "type": "message",
            "data": {
                "id": str(uuid4()),
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
        }
        await manager.send_message(self.client_id, message)
        
    async def send_function_call(self, function_name: str, args: dict):
        message = {
            "type": "function_call",
            "data": {
                "function": function_name,
                "args": args,
                "timestamp": datetime.now().isoformat()
            }
        }
        await manager.send_message(self.client_id, message)
        
    async def get_user_input(self, prompt: str) -> str:
        # Send input request
        message = {
            "type": "input_request",
            "data": {
                "prompt": prompt,
                "timestamp": datetime.now().isoformat()
            }
        }
        await manager.send_message(self.client_id, message)
        
        # Wait for response (this is simplified - in real implementation you'd use proper async waiting)
        return "continue"  # Default response

async def run_travel_workflow(client_id: str, user_message: str):
    ui = SimpleUI(client_id)
    
    # Send initial message if it's the first interaction
    if not manager.conversations[client_id]:
        await ui.send_message("assistant", INITIAL_MESSAGE)
    
    # Create agents
    with llm_config:
        travel_agent = ConversableAgent(
            name="travel_agent",
            system_message=SYSTEM_MESSAGE,
            human_input_mode="NEVER"
        )

    customer = ConversableAgent(
        name="customer",
        human_input_mode="NEVER",
    )

    # Register functions
    register_function(
        lookup_member,
        caller=travel_agent,
        executor=customer,
        description="Look up member details from the database"
    )

    register_function(
        create_itinerary,
        caller=travel_agent,
        executor=customer,
        description="Create a personalized travel itinerary based on member details"
    )

    # Send user message
    await ui.send_message("user", user_message)
    
    # Run conversation
    try:
        response = customer.initiate_chat(
            travel_agent,
            message=user_message,
            max_turns=1
        )
        
        # Send agent response
        if response and hasattr(response, 'summary'):
            await ui.send_message("assistant", response.summary)
        elif response and hasattr(response, 'chat_history'):
            last_message = response.chat_history[-1]
            if 'content' in last_message:
                await ui.send_message("assistant", last_message['content'])
            
    except Exception as e:
        await ui.send_message("assistant", f"Sorry, I encountered an error: {str(e)}")

app = FastAPI(title="Simple Travel Agent")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "user_message":
                user_message = message_data["content"]
                await run_travel_workflow(client_id, user_message)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@app.get("/")
async def get():
    return {"message": "Simple Travel Agent Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
