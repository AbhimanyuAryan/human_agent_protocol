import os
import asyncio
import threading
from typing import Annotated, Any, Optional, Dict
from uuid import uuid4
from dotenv import load_dotenv
import logging

# Set up comprehensive logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"🌍 [STARTUP] Loading environment variables")
load_dotenv()

logger.info(f"🚀 [STARTUP] Starting imports")
# Import AutoGen components for agent creation and interaction
from autogen import ConversableAgent, LLMConfig, register_function

# FastAPI for creating the web server
from fastapi import FastAPI

# Fastagency for UI interactions and workflow management
from fastagency import UI
from src.ag_ui_ag2.ag_ui_adapter import AGUIAdapter
from fastagency.runtimes.ag2 import Workflow

# Local project imports for database access and message templates
from src.ag_ui_ag2.database import MEMBER_DATABASE
from src.ag_ui_ag2.messages import SYSTEM_MESSAGE, INITIAL_MESSAGE
logger.info(f"🚀 [STARTUP] All imports completed successfully")

# Thread-local storage for tracking thread IDs
# This helps manage state across different conversation threads
thread_local = threading.local()

# Travel agent function to look up member information
def lookup_member(
    member_id: Annotated[str, "User's membership ID"]
) -> dict[str, Any]:
    """Look up member details with comprehensive logging."""
    logger.info(f"🔍 [LOOKUP] lookup_member called with member_id: '{member_id}'")
    logger.debug(f"🔍 [LOOKUP] Available member IDs: {list(MEMBER_DATABASE.keys())}")
    
    if member_id in MEMBER_DATABASE:
        result = {
            "found": True,
            "name": MEMBER_DATABASE[member_id]["name"],
            "membership": MEMBER_DATABASE[member_id]["membership"],
            "preferences": MEMBER_DATABASE[member_id]["preferences"]
        }
        logger.info(f"✅ [LOOKUP] Member found: {result}")
        return result
    else:
        result = {
            "found": False,
            "message": "Member ID not found in our system"
        }
        logger.info(f"❌ [LOOKUP] Member not found: {result}")
        return result

# Function to create personalized itinerary
def create_itinerary(
    destination: Annotated[str, "Travel destination (e.g., New York, Paris, Tokyo)"],
    days: Annotated[int, "Number of days for the trip"],
    membership_type: Annotated[str, "Type of membership (premium or standard)"],
    preferences: Annotated[list, "Traveler preferences (e.g., fine dining, cultural tours)"]
) -> dict[str, Any]:
    """Create travel itinerary with comprehensive logging."""
    logger.info(f"🗓️ [ITINERARY] create_itinerary called")
    logger.info(f"🗓️ [ITINERARY] destination: '{destination}'")
    logger.info(f"🗓️ [ITINERARY] days: {days}")
    logger.info(f"🗓️ [ITINERARY] membership_type: '{membership_type}'")
    logger.info(f"🗓️ [ITINERARY] preferences: {preferences}")
    
    if not destination or days <= 0:
        error_result = {"error": "Invalid destination or number of days."}
        logger.error(f"❌ [ITINERARY] Invalid parameters: {error_result}")
        return error_result

    logger.info(f"🗓️ [ITINERARY] Creating itinerary for {days} days")
    itinerary = []
    for day in range(1, days + 1):
        day_plan = {
            "day": f"Day {day}",
            "morning": "",
            "afternoon": "",
            "evening": "",
        }

        # Differentiate activities based on membership type
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
    logger.info(f"✅ [ITINERARY] Itinerary created successfully for {destination}")
    return result

logger.info(f"🤖 [LLM] Configuring LLM")
# Configure LLM
llm_config = LLMConfig(
    model="gpt-4o-mini",  # Specify which OpenAI model to use
    api_key=os.getenv("OPENAI_API_KEY"),  # Get API key from environment variables
)
logger.info(f"🤖 [LLM] LLM configuration complete")

logger.info(f"🔄 [WORKFLOW] Initializing workflow")
# Initialize the workflow manager
wf = Workflow()

@wf.register(name="hitl_workflow", description="A simple travel itinerary generator workflow")
def hitl_workflow(ui: UI, params: dict[str, Any]) -> str:
    """Main workflow with comprehensive debug logging."""
    logger.info(f"🚀 [WORKFLOW] hitl_workflow started")
    logger.info(f"🚀 [WORKFLOW] UI type: {type(ui)}")
    logger.info(f"🚀 [WORKFLOW] Params: {params}")
    
    try:
        logger.info(f"💬 [WORKFLOW] Displaying initial message")
        initial_message = ui.text_input(
            sender="Workflow",
            recipient="User",
            prompt=INITIAL_MESSAGE,
        )
        logger.info(f"💬 [WORKFLOW] Initial message received: {initial_message}")
        
        logger.info(f"🤖 [WORKFLOW] Creating agents")
        with llm_config:
            travel_agent = ConversableAgent(
                name="travel_agent",
                system_message=SYSTEM_MESSAGE
            )
            logger.info(f"🤖 [WORKFLOW] Travel agent created")

        customer = ConversableAgent(
            name="customer",
            human_input_mode="ALWAYS",
        )
        logger.info(f"🤖 [WORKFLOW] Customer agent created")

        logger.info(f"🔧 [WORKFLOW] Registering functions")
        register_function(
            lookup_member,
            caller=travel_agent,
            executor=customer,
            description="Look up member details from the database"
        )
        logger.info(f"🔧 [WORKFLOW] lookup_member function registered")

        register_function(
            create_itinerary,
            caller=travel_agent,
            executor=customer,
            description="Create a personalized travel itinerary based on member details"
        )
        logger.info(f"🔧 [WORKFLOW] create_itinerary function registered")

        logger.info(f"🗣️ [WORKFLOW] Starting conversation")
        response = customer.run(
            travel_agent,
            message=initial_message,
            summary_method="reflection_with_llm"
        )
        
        logger.info(f"📝 [WORKFLOW] Conversation completed")
        result = ui.process(response)
        logger.info(f"✅ [WORKFLOW] Workflow completed successfully")
        
        return result  # type: ignore[no-any-return]
        
    except Exception as e:
        logger.error(f"💥 [WORKFLOW] Error in hitl_workflow: {e}")
        import traceback
        logger.error(f"💥 [WORKFLOW] Traceback: {traceback.format_exc()}")
        raise

def without_customer_messages(message: Any) -> bool:
    """Filter function with debug logging."""
    logger.debug(f"🔧 [FILTER] Filtering message: {type(message)} - {getattr(message, 'type', 'no type')}")
    result = not (message.type == "text" and message.content.sender == "customer")
    logger.debug(f"🔧 [FILTER] Filter result: {result}")
    return result

logger.info(f"🔗 [ADAPTER] Creating AGUIAdapter")
# Create an adapter that connects our workflow to the AG-UI protocol
adapter = AGUIAdapter(
    provider=wf,
    wf_name="hitl_workflow",
    filter=without_customer_messages
)
logger.info(f"🔗 [ADAPTER] AGUIAdapter created successfully")

logger.info(f"🌐 [APP] Creating FastAPI application")
# Create FastAPI application and include the adapter's router
app = FastAPI()
app.include_router(adapter.router)
logger.info(f"🌐 [APP] FastAPI application created and router included")
logger.info(f"✅ [STARTUP] Application initialization complete")
