import os
import asyncio
import json
import logging
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"🔍 lookup_member called with member_id: '{member_id}'")
    
    if member_id in MEMBER_DATABASE:
        result = {
            "found": True,
            "name": MEMBER_DATABASE[member_id]["name"],
            "membership": MEMBER_DATABASE[member_id]["membership"],
            "preferences": MEMBER_DATABASE[member_id]["preferences"]
        }
        logger.info(f"✅ Member found: {result}")
        return result
    else:
        result = {
            "found": False,
            "message": "Member ID not found in our system"
        }
        logger.info(f"❌ Member not found: {result}")
        return result

def create_itinerary(
    destination: str,
    days: int,
    membership_type: str,
    preferences: list
) -> dict[str, Any]:
    """Create a realistic, personalized travel itinerary"""
    logger.info(f"🗓️ create_itinerary called with destination: '{destination}', days: {days}, membership: '{membership_type}', preferences: {preferences}")
    
    if not destination or days <= 0:
        error_result = {"error": "Invalid destination or number of days."}
        logger.error(f"❌ Invalid parameters: {error_result}")
        return error_result

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

    result = {
        "destination": destination,
        "days": days,
        "itinerary": itinerary,
        "accommodation": "5-star hotel" if membership_type == "premium" else "3-star or boutique hotel",
        "transportation": "Private car service" if membership_type == "premium" else "Local transport and shared rides",
        "is_draft": True
    }
    logger.info(f"✅ Itinerary created successfully for {destination}")
    return result

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
    logger.info(f"🚀 Starting workflow for client {client_id} with message: '{user_message}'")
    ui = SimpleUI(client_id)
    
    # Send initial message if it's the first interaction
    if not manager.conversations[client_id]:
        logger.info(f"💬 Sending initial message to new client {client_id}")
        await ui.send_message("assistant", INITIAL_MESSAGE)
    
    # Create agents
    logger.info(f"🤖 Creating agents for client {client_id}")
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
    logger.info(f"🔧 Registering functions for client {client_id}")
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
    logger.info(f"📤 Sending user message to UI: '{user_message}'")
    await ui.send_message("user", user_message)
    
    # Run conversation
    try:
        logger.info(f"🗣️ Starting chat between customer and travel_agent")
        response = customer.initiate_chat(
            travel_agent,
            message=user_message,
            max_turns=1
        )
        
        logger.info(f"📝 Chat response received: {type(response)}")
        if hasattr(response, 'summary'):
            logger.info(f"📋 Response summary: {response.summary}")
        if hasattr(response, 'chat_history'):
            logger.info(f"📚 Chat history length: {len(response.chat_history) if response.chat_history else 0}")
            if response.chat_history:
                for i, msg in enumerate(response.chat_history):
                    logger.info(f"📜 Message {i}: {msg}")
        
        # Send agent response
        if response and hasattr(response, 'summary') and response.summary:
            logger.info(f"✅ Sending summary to client: {response.summary}")
            await ui.send_message("assistant", response.summary)
        elif response and hasattr(response, 'chat_history') and response.chat_history:
            last_message = response.chat_history[-1]
            logger.info(f"📤 Processing last message: {last_message}")
            
            if isinstance(last_message, dict) and 'content' in last_message:
                content = last_message['content']
                logger.info(f"📝 Message content: {content}")
                
                # Skip tool call debug messages
                if not content.startswith("***** Suggested tool call") and not content.startswith("****"):
                    logger.info(f"✅ Sending content to client: {content}")
                    await ui.send_message("assistant", content)
                else:
                    logger.info(f"🚫 Skipping tool call debug message")
            else:
                logger.warning(f"⚠️ Unexpected message format: {last_message}")
        else:
            logger.warning(f"⚠️ No valid response found, sending fallback message")
            await ui.send_message("assistant", "I'm ready to help you plan your trip!")
            
    except Exception as e:
        logger.error(f"💥 Error in workflow: {str(e)}", exc_info=True)
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
    logger.info(f"🔌 WebSocket connection established for client: {client_id}")
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"📨 Received WebSocket data from {client_id}: {data}")
            
            message_data = json.loads(data)
            logger.info(f"📋 Parsed message data: {message_data}")
            
            if message_data["type"] == "user_message":
                user_message = message_data["content"]
                logger.info(f"👤 Processing user message: '{user_message}'")
                await run_travel_workflow(client_id, user_message)
            else:
                logger.warning(f"⚠️ Unknown message type: {message_data['type']}")
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for client: {client_id}")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"💥 WebSocket error for client {client_id}: {str(e)}", exc_info=True)
        manager.disconnect(client_id)

@app.get("/")
async def get():
    return {"message": "Simple Travel Agent Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
