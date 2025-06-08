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

class AgentContext:
    def __init__(self):
        self.travel_agent = None
        self.customer = None
        self.initialized = False
        self.conversation_history = []  # Track full conversation

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversations: Dict[str, list] = {}
        self.agent_contexts: Dict[str, AgentContext] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.conversations[client_id] = []
        self.agent_contexts[client_id] = AgentContext()
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.conversations:
            del self.conversations[client_id]
        if client_id in self.agent_contexts:
            del self.agent_contexts[client_id]
            
    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific client via WebSocket"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
                logger.info(f"📤 Sent message to client {client_id}: {message['type']}")
            except Exception as e:
                logger.error(f"❌ Failed to send message to client {client_id}: {e}")
                # Remove the connection if it's broken
                self.disconnect(client_id)
        else:
            logger.warning(f"⚠️ Client {client_id} not found in active connections")

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
    
    # Get or create agent context for this client
    context = manager.agent_contexts[client_id]
    
    # Send initial message if it's the first interaction
    if not manager.conversations[client_id]:
        logger.info(f"💬 Sending initial message to new client {client_id}")
        await ui.send_message("assistant", INITIAL_MESSAGE)
        manager.conversations[client_id].append({"role": "assistant", "content": INITIAL_MESSAGE})
    
    # Initialize agents only once per client
    if not context.initialized:
        logger.info(f"🤖 Creating agents for client {client_id}")
        with llm_config:
            context.travel_agent = ConversableAgent(
                name="travel_agent",
                system_message=SYSTEM_MESSAGE,
                human_input_mode="NEVER"
            )

        context.customer = ConversableAgent(
            name="customer",
            human_input_mode="NEVER",
        )

        # Register functions
        logger.info(f"🔧 Registering functions for client {client_id}")
        register_function(
            lookup_member,
            caller=context.travel_agent,
            executor=context.customer,
            description="Look up member details from the database"
        )

        register_function(
            create_itinerary,
            caller=context.travel_agent,
            executor=context.customer,
            description="Create a personalized travel itinerary based on member details"
        )
        
        context.initialized = True

    # Add user message to conversation history
    manager.conversations[client_id].append({"role": "user", "content": user_message})
    context.conversation_history.append({"role": "user", "content": user_message})

    # Send user message
    logger.info(f"📤 Sending user message to UI: '{user_message}'")
    await ui.send_message("user", user_message)
    
    try:
        # Build conversation context from history
        conversation_context = []
        for msg in context.conversation_history:
            if msg["role"] == "user":
                conversation_context.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                conversation_context.append(f"Assistant: {msg['content']}")
        
        # Create context-aware message
        if len(conversation_context) > 1:
            context_message = "Conversation so far:\n" + "\n".join(conversation_context[:-1]) + f"\n\nUser's latest message: {user_message}"
        else:
            context_message = user_message

        logger.info(f"🗣️ Starting chat with context: {context_message}")
        
        # Use the persistent agents instead of creating new ones
        response = context.customer.initiate_chat(
            context.travel_agent,
            message=context_message,
            max_turns=3,  # Allow multiple turns for tool execution
            silent=True
        )
        
        logger.info(f"📝 Chat response received: {type(response)}")
        if hasattr(response, 'summary'):
            logger.info(f"📋 Response summary: {response.summary}")
        if hasattr(response, 'chat_history'):
            logger.info(f"📚 Chat history length: {len(response.chat_history) if response.chat_history else 0}")
            if response.chat_history:
                for i, msg in enumerate(response.chat_history):
                    logger.info(f"📜 Message {i}: {msg}")
        
        # Process response and handle tool calls
        assistant_response = None
        
        if response and hasattr(response, 'chat_history') and response.chat_history:
            # Look for the travel agent's response in the chat history
            for message in reversed(response.chat_history):
                if isinstance(message, dict):
                    # Handle tool calls
                    if 'tool_calls' in message and message['tool_calls']:
                        logger.info(f"🔧 Tool call detected: {message['tool_calls'][0]['function']['name']}")
                        
                        tool_call = message['tool_calls'][0]
                        function_name = tool_call['function']['name']
                        function_args = json.loads(tool_call['function']['arguments'])
                        
                        await ui.send_function_call(function_name, function_args)
                        
                        # Execute the function call
                        if function_name == "lookup_member":
                            result = lookup_member(function_args.get('member_id', ''))
                            logger.info(f"🔍 lookup_member result: {result}")
                            
                            if result.get('found'):
                                assistant_response = f"Great! I found your profile, {result['name']}. You have {result['membership']} membership with preferences for {', '.join(result['preferences'])}. Now, could you please tell me your desired destination and travel dates?"
                            else:
                                assistant_response = "I couldn't find that member ID in our system. Could you please double-check and provide your member ID again?"
                                
                        elif function_name == "create_itinerary":
                            result = create_itinerary(
                                function_args.get('destination', ''),
                                function_args.get('days', 0),
                                function_args.get('membership_type', ''),
                                function_args.get('preferences', [])
                            )
                            logger.info(f"🗓️ create_itinerary result: {result}")
                            
                            if 'error' not in result:
                                itinerary_text = f"Here's your personalized {result['days']}-day itinerary for {result['destination']}:\n\n"
                                for day_plan in result['itinerary']:
                                    itinerary_text += f"{day_plan['day']}:\n"
                                    itinerary_text += f"  Morning: {day_plan['morning']}\n"
                                    itinerary_text += f"  Afternoon: {day_plan['afternoon']}\n"
                                    itinerary_text += f"  Evening: {day_plan['evening']}\n\n"
                                itinerary_text += f"Accommodation: {result['accommodation']}\n"
                                itinerary_text += f"Transportation: {result['transportation']}\n\n"
                                itinerary_text += "This is a draft itinerary. Would you like me to make any adjustments?"
                                assistant_response = itinerary_text
                            else:
                                assistant_response = f"Error creating itinerary: {result['error']}"
                        break
                    
                    # Handle regular text messages
                    elif 'content' in message and message['content'] and message.get('name') == 'travel_agent':
                        content = message['content']
                        if not content.startswith("***** Suggested tool call") and not content.startswith("****"):
                            assistant_response = content
                            break
        
        # Use summary as fallback
        if not assistant_response and response and hasattr(response, 'summary') and response.summary:
            assistant_response = response.summary
            
        # Send final fallback message if nothing else worked
        if not assistant_response:
            assistant_response = "I'm ready to help you plan your trip!"
        
        # Send the assistant's response and add to history
        await ui.send_message("assistant", assistant_response)
        manager.conversations[client_id].append({"role": "assistant", "content": assistant_response})
        context.conversation_history.append({"role": "assistant", "content": assistant_response})
        
    except Exception as e:
        logger.error(f"💥 Error in workflow: {str(e)}", exc_info=True)
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        await ui.send_message("assistant", error_msg)
        manager.conversations[client_id].append({"role": "assistant", "content": error_msg})
        context.conversation_history.append({"role": "assistant", "content": error_msg})

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
