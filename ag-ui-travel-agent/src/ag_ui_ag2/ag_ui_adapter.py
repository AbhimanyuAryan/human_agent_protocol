import asyncio
import threading
from asyncio import Queue
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, AsyncIterator, Callable, Optional
from uuid import uuid4
from datetime import datetime

import autogen
import autogen.messages
import autogen.messages.agent_messages
import autogen.events.agent_events
from src.types import (
    BaseMessage,
    CustomEvent,
    EventType,
    RunAgentInput,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    UserMessage,
    StateSnapshotEvent,
    StateDeltaEvent,
)
from src.encoder import EventEncoder
from asyncer import asyncify, syncify
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from fastagency.logging import get_logger

# Fix relative imports by using absolute imports
from fastagency.base import (
    CreateWorkflowUIMixin,
    ProviderProtocol,
    Runnable,
    UIBase,
)
from fastagency.exceptions import (
    FastAgencyConnectionError,
    FastAgencyKeyError,
)
from fastagency.messages import (
    IOMessage,
    InitiateWorkflowModel,
    MessageProcessorMixin,
    TextInput,
    TextMessage,
)

# Import tool call event classes
from ag_ui_ag2.tool_events import (
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
)

#------------------------------------------------------------------------------
# DATA MODELS AND THREAD MANAGEMENT
#------------------------------------------------------------------------------

class WorkflowInfo(BaseModel):
    name: str
    description: str


# thread is used here in context of Agent User Interaction Protocol thread, not python threading


class AGUIThreadInfo:
    def __init__(self, run_agent_input: RunAgentInput, workflow_id: str) -> None:
        """Represent AG-UI thread.
        
        This class stores all information related to a specific Agent-UI interaction thread.
        It manages message queues, encoding, state tracking, and thread lifecycle.
        
        Args:
            run_agent_input (RunAgentInput): Input parameters from the UI client request
            workflow_id (str): Unique identifier for the associated workflow
        """
        # Store the original request input for reference
        self.run_agent_input = run_agent_input
        
        # Extract key identifiers from the input
        self.thread_id = run_agent_input.thread_id  # Unique ID for this UI thread
        self.run_id = run_agent_input.run_id        # Unique ID for this execution run
        self.workflow_id = workflow_id              # ID of the associated workflow
        
        # Communication channels for async message passing
        self.out_queue: Queue[BaseMessage] = Queue()  # Messages from agent to UI
        self.input_queue: Queue[str] = Queue()        # User inputs from UI to agent
        
        # Thread status tracking
        self.active = True  # Whether this thread is still active
        
        # Message serialization utility
        self.encoder = EventEncoder()
        
        # Message history for debugging and state recovery
        self.sent_messages: list[BaseMessage] = []  # Record of all sent messages
        
        # State management for tracking workflow progress and data
        self.state: dict = {}    
        
    def has_text_input_widget(self) -> bool:
        """Check if this thread has a text input widget active.
        
        Returns:
            bool: True if the thread has an active text input widget, False otherwise
                  This implementation always returns False but can be overridden in subclasses
        """
        return False

    def next_message_id(self) -> str:
        """Generate a unique message identifier for new messages.
        
        Creates a UUID-based hex string to uniquely identify messages sent in this thread.
        
        Returns:
            str: A unique message identifier string
        """
        return str(uuid4().hex)
        
    def update_state(self, delta: dict) -> None:
        """Update thread state with incremental changes.
        
        Updates the thread's state dictionary with the provided delta changes,
        allowing for partial state updates without replacing the entire state.
        
        Args:
            delta (dict): Key-value pairs of state changes to apply
        """
        self.state.update(delta)


workflow_ids = threading.local()
workflow_ids.workflow_uuid = None


#------------------------------------------------------------------------------
# MAIN ADAPTER CLASS AND PROTOCOL IMPLEMENTATION
#------------------------------------------------------------------------------

class AGUIAdapter(MessageProcessorMixin, CreateWorkflowUIMixin):    
    def __init__(
        self,
        provider: ProviderProtocol,
        *,
        discovery_path: str = "/fastagency/discovery",
        agui_path: str = "/fastagency/agui",
        wf_name: Optional[str] = None,
        get_user_id: Optional[Callable[..., Optional[str]]] = None,
        filter: Optional[Callable[[BaseMessage], bool]] = None,
    ) -> None:
        """Provider for AG-UI.

        This adapter connects FastAgency workflows with AG-UI interfaces, handling
        message routing, thread management, and real-time communication between
        agents and the frontend UI.
        
        Args:
            provider (ProviderProtocol): The workflow provider that executes agent workflows
            discovery_path (str, optional): API path for workflow discovery endpoint. Defaults to "/fastagency/discovery".
            agui_path (str, optional): API path for AG-UI communication endpoint. Defaults to "/fastagency/agui".
            wf_name (str, optional): Name of the default workflow to run. If None, uses the first available workflow.
            get_user_id (Optional[Callable[..., Optional[str]]], optional): Function to extract user ID from requests. Defaults to None.
            filter (Optional[Callable[[BaseMessage], bool]], optional): Optional filter function for messages. Defaults to None.
        """
        # Store configuration and dependencies
        self.provider = provider
        self.discovery_path = discovery_path
        self.agui_path = agui_path
        self.get_user_id = get_user_id or (lambda: None)
        
        # Initialize thread management
        self._agui_threads: dict[str, AGUIThreadInfo] = {}
        
        # Determine the default workflow name
        if wf_name is None:
            wf_name = self.provider.names[0]
        self.wf_name = wf_name
        
        # Set up the API router with endpoints
        self.router = self.setup_routes()
        
        # Store the optional message filter
        self.filter = filter    
        
    def visit(self, message: IOMessage) -> Optional[str]:
        """Process an incoming IO message with optional filtering.
        
        This is the primary entry point for message processing. It applies the optional
        filter function before passing messages to the appropriate handler methods.
        
        Args:
            message (IOMessage): The message to process
            
        Returns:
            Optional[str]: Result from message processing, if any
        """
        if self.filter and not self.filter(message):
            logger.info(f"Message filtered out: {message}")
            return None
        # call the super class visit method
        return super().visit(message)
    
    def get_thread_info_of_workflow(
        self, workflow_uuid: str
    ) -> Optional[AGUIThreadInfo]:
        """Retrieve thread information associated with a specific workflow UUID.
        
        Finds the first thread that is linked to the given workflow UUID.
        
        Args:
            workflow_uuid (str): The unique identifier for the workflow
            
        Returns:
            Optional[AGUIThreadInfo]: Thread information if found, None otherwise
            
        Raises:
            RuntimeError: If the workflow is not found in any registered threads
        """
        thread_info = next(
            (x for x in self._agui_threads.values() if x.workflow_id == workflow_uuid),
            None,
        )
        if thread_info is None:
            logger.error(
                f"Workflow {workflow_uuid} not found in threads: {self._agui_threads}"
            )
            raise RuntimeError(
                f"Workflow {workflow_uuid} not found in threads: {self._agui_threads}"
            )
        return thread_info

    def get_thread_info_of_agui(self, thread_id: str) -> Optional[AGUIThreadInfo]:
        """Get thread information by AG-UI thread ID.
        
        Args:
            thread_id (str): The unique identifier for the AG-UI thread
            
        Returns:
            Optional[AGUIThreadInfo]: Thread information if found, None otherwise
        """
        return self._agui_threads.get(thread_id)

    def send_to_thread(self, thread_id: str, message: str) -> None:
        """Send a message to a specific AG-UI thread.
        
        Args:
            thread_id (str): The target thread identifier
            message (str): The message to send
        """
        thread_info = self._agui_threads.get(thread_id)
        if thread_info:
            if not thread_info.active:
                logger.error(f"Thread {thread_id} is not active")
                return
            thread_info.out_queue.put_nowait(message)
        else:
            logger.error(f"Thread {thread_id} not found")

    def end_of_thread(self, thread_id: str) -> None:
        """Terminate an AG-UI thread and clean up resources.
        
        Removes the thread from the active threads dictionary and marks it as inactive.
        
        Args:
            thread_id (str): The identifier of the thread to terminate
        """
        thread_info = self._agui_threads.pop(thread_id, None)
        if thread_info:
            thread_info.active = False
            logger.info(f"Ended AG-UI thread: {thread_info}")
    async def run_thread(
        self, input: RunAgentInput, request: Request
    ) -> AsyncIterator[str]:
        """Run an AG-UI thread and stream events back to the client.
        
        This method establishes a Server-Sent Events (SSE) connection with the client and
        continuously polls the thread's output queue for messages to send to the frontend.
        The connection remains open until:
        1. The client disconnects
        2. A RunFinishedEvent is received 
        3. A CustomEvent with name "thread_over" is received
        
        Args:
            input: Client input containing thread identification
            request: The HTTP request object for checking connection status
            
        Yields:
            String-encoded event messages for SSE streaming
            
        Raises:
            RuntimeError: If the specified thread is not found
        """
        # Retrieve thread information or fail if not found
        thread_info = self._agui_threads.get(input.thread_id)
        if thread_info is None:
            logger.error(f"Thread {input.thread_id} not found")
            raise RuntimeError(f"Thread {input.thread_id} not found")

        # Send run started event first
        run_started = RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=thread_info.thread_id,
            run_id=thread_info.run_id,
        )
        yield self._sse_send(run_started, thread_info)

        # Then send initial state snapshot
        initial_state = {
            "status": {
                "phase": "initialized",
                "error": None,
                "timestamp": datetime.now().isoformat()
            },              "conversation": {
                "stage": "starting",
                "messages": [
                    {
                        "id": "placeholder",
                        "role": "assistant",
                        "content": "",
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "tools": [],
                "completed": False
            },
            "agent": {
                "name": "Travel Assistant",
                "capabilities": ["search", "recommend", "book"],
                "current_task": None
            },
            "ui": {
                "showProgress": True,
                "activeTab": "chat",
                "loading": False,
                "showInput": False
            }
        }
        
        state_snapshot = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=initial_state
        )
        yield self._sse_send(state_snapshot, thread_info)

        # Update state to show processing has started
        processing_delta = [
            {
                "op": "replace",
                "path": "/status/phase",
                "value": "processing"
            },
            {
                "op": "replace",
                "path": "/ui/loading",
                "value": True
            },
            {
                "op": "replace",
                "path": "/agent/current_task",
                "value": "Processing your request..."
            }
        ]
        state_delta = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=processing_delta
        )
        yield self._sse_send(state_delta, thread_info)

        # Main event loop: keep checking for messages until client disconnects
        while not await request.is_disconnected():
            try:
                # Try to get a message from queue with timeout to avoid blocking
                message = await asyncio.wait_for(
                    thread_info.out_queue.get(), timeout=0.5
                )
                
                # If this is a RunFinishedEvent, we need to check if there are any pending state updates
                if isinstance(message, RunFinishedEvent):
                    # Send any pending state updates before RUN_FINISHED
                    completion_delta = [
                        {
                            "op": "replace",
                            "path": "/status/phase",
                            "value": "completed"
                        },
                        {
                            "op": "replace",
                            "path": "/ui/loading",
                            "value": False
                        },
                        {
                            "op": "replace",
                            "path": "/agent/current_task",
                            "value": None
                        }
                    ]
                    state_delta = StateDeltaEvent(
                        type=EventType.STATE_DELTA,
                        delta=completion_delta
                    )
                    yield self._sse_send(state_delta, thread_info)
                    
                    # Now send the RUN_FINISHED event
                    yield self._sse_send(message, thread_info)
                    break
                
                # For thread over condition, send state updates before RUN_FINISHED
                elif isinstance(message, CustomEvent) and message.name == "thread_over":
                    # Update state for thread completion before ending the run
                    thread_over_delta = [
                        {
                            "op": "replace",
                            "path": "/status/phase",
                            "value": "thread_completed"
                        },
                        {
                            "op": "replace",
                            "path": "/conversation/completed",
                            "value": True
                        },
                        {
                            "op": "replace",
                            "path": "/ui/loading",
                            "value": False
                        }
                    ]
                    state_delta = StateDeltaEvent(
                        type=EventType.STATE_DELTA,
                        delta=thread_over_delta
                    )
                    yield self._sse_send(state_delta, thread_info)
                    
                    # Send the thread over event
                    yield self._sse_send(message, thread_info)
                    
                    # Send RUN_FINISHED after all state updates
                    run_finished = RunFinishedEvent(
                        type=EventType.RUN_FINISHED,
                        thread_id=thread_info.thread_id,
                        run_id=thread_info.run_id,
                    )
                    yield self._sse_send(run_finished, thread_info)
                    
                    logger.info(f"Thread {input.thread_id} is over")
                    self.end_of_thread(input.thread_id)
                    break
                
                # For all other messages, just send them as is
                else:
                    yield self._sse_send(message, thread_info)
                
            except asyncio.TimeoutError:
                await asyncio.sleep(0)
                continue
            except Exception as e:
                # Send error state updates before RUN_FINISHED
                error_delta = [
                    {
                        "op": "replace",
                        "path": "/status/phase",
                        "value": "error"
                    },
                    {
                        "op": "replace",
                        "path": "/status/error",
                        "value": str(e)
                    },
                    {
                        "op": "replace",
                        "path": "/ui/loading",
                        "value": False
                    }
                ]
                state_delta = StateDeltaEvent(
                    type=EventType.STATE_DELTA,
                    delta=error_delta
                )
                yield self._sse_send(state_delta, thread_info)
                
                # Send RUN_FINISHED after error state updates
                run_finished = RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=thread_info.thread_id,
                    run_id=thread_info.run_id,
                )
                yield self._sse_send(run_finished, thread_info)
                
                logger.error(f"Error in thread {input.thread_id}: {str(e)}")
                break

        logger.info(f"Run thread {input.thread_id} completed")

    def _sse_send(self, message: BaseMessage, thread_info: AGUIThreadInfo) -> str:
        """Format and encode a message for Server-Sent Events (SSE) transmission.
        
        This utility method records the message in the thread's history and 
        converts it to a properly formatted SSE string.
        
        Args:
            message: The message to send
            thread_info: The thread context for this message
            
        Returns:
            A properly formatted SSE event string
        """
        thread_info.sent_messages.append(message)
        return str(thread_info.encoder.encode(message))
    
    def setup_routes(self) -> APIRouter:
        """Set up FastAPI routes for AG-UI communication.
        
        Creates an APIRouter with two main endpoints:
        1. AGUI endpoint for handling real-time client connections
        2. Discovery endpoint for allowing clients to find available workflows
        
        Returns:
            APIRouter: Configured router with AG-UI endpoints
        """
        router = APIRouter()        
        
        @router.post(self.agui_path)
        async def run_agent(
            input: RunAgentInput,
            request: Request,
            user_id: Optional[str] = Depends(self.get_user_id),
        ) -> StreamingResponse:
            # Set HTTP headers for Server-Sent Events (SSE) streaming response
            headers = {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Nginx: prevent buffering
            }

            # CASE 1: Resuming an existing thread (e.g., after user sends a message)
            if input.thread_id in self._agui_threads:
                logger.info(f"Resuming thread: {input.thread_id}")
                logger.info(f"Messages: {input.messages}")
                
                # Get the existing thread context
                thread_info = self._agui_threads[input.thread_id]
                
                # Process any new user messages that triggered this request
                last_message = input.messages[-1]
                if isinstance(last_message, UserMessage):
                    thread_info.input_queue.put_nowait(last_message.content)
                
                # Continue the streaming connection
                return StreamingResponse(
                    self.run_thread(input, request), headers=headers
                )            # CASE 2: Creating a new thread for a first-time conversation
            # Generate a unique workflow ID for this thread
            workflow_uuid: str = uuid4().hex

            # Create and register a new thread info object
            thread_info = AGUIThreadInfo(input, workflow_id=workflow_uuid)
            self._agui_threads[input.thread_id] = thread_info
            logger.info(f"Created new thread: {input.thread_id}")

            # Prepare workflow initialization message
            init_msg = InitiateWorkflowModel(
                user_id=user_id,
                workflow_uuid=workflow_uuid,
                params={},
                name=self.wf_name,
            )

            # Define a nested function to execute the workflow in the background
            async def process_messages_in_background(workflow_uuid: str) -> None:
                def a_process_messages_in_background(
                    workflow_uuid: str,
                ) -> None:
                    # Store workflow ID in thread-local storage for access by handlers
                    workflow_ids.workflow_uuid = workflow_uuid
                    
                    # Execute the workflow with the provider
                    self.provider.run(
                        name=init_msg.name,
                        ui=self.create_workflow_ui(workflow_uuid),
                        user_id=user_id if user_id else "None",
                        **init_msg.params,
                    )

                # Convert the synchronous function to run asynchronously
                await asyncify(a_process_messages_in_background)(workflow_uuid)
                # Clear thread-local storage when done
                workflow_ids.workflow_uuid = None

            try:
                # Start the background task for processing workflow messages
                task = asyncio.create_task(
                    process_messages_in_background(workflow_uuid)
                )
                logger.info(f"Started task: {task}")
            except Exception as e:
                logger.error(f"Error in AG-UI endpoint: {e}", stack_info=True)
            finally:
                pass
                # self.end_of_thread(request.thread_id)
                
            # Return a streaming response to establish the SSE connection
            return StreamingResponse(self.run_thread(input, request), headers=headers)        
        
        @router.get(
            self.discovery_path,
            responses={
                404: {"detail": "Key Not Found"},
                504: {"detail": "Unable to connect to provider"},
            },
        )
        def discovery(
            user_id: Optional[str] = Depends(self.get_user_id),
        ) -> list[WorkflowInfo]:
            """Endpoint that provides information about available workflows.
            
            This endpoint allows clients to discover what workflows are available
            in the system and their descriptions. Used for populating UI dropdowns
            or other workflow selection interfaces.
            
            Args:
                user_id: Optional user identifier from the dependency
                
            Returns:
                List of WorkflowInfo objects with name and description
                
            Raises:
                HTTPException 504: If connection to provider fails
                HTTPException 404: If requested workflow is not found
            """
            # Step 1: Get available workflow names from the provider
            try:
                names = self.provider.names
            except FastAgencyConnectionError as e:
                raise HTTPException(status_code=504, detail=str(e)) from e

            # Step 2: Get descriptions for each workflow
            try:
                descriptions = [self.provider.get_description(name) for name in names]
            except FastAgencyKeyError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e

            # Step 3: Create WorkflowInfo objects with name and description pairs
            return [
                WorkflowInfo(name=name, description=description)
                for name, description in zip(names, descriptions)
            ]

        return router
        
    #------------------------------------------------------------------------------
    # MESSAGE HANDLERS AND EVENT PROCESSING
    #------------------------------------------------------------------------------
    def visit_default(self, message: IOMessage) -> Optional[str]:
        """Default message handler for otherwise unhandled message types.
        
        This is a fallback method that logs unknown messages but doesn't process them further.
        It converts the synchronous method call to an asynchronous one for consistency
        with other message handlers.
        
        Args:
            message: The message to process
            
        Returns:
            None, as default handling simply logs the message
        """
        async def a_visit_default(
            self: AGUIAdapter, message: IOMessage, workflow_uuid: str
        ) -> Optional[str]:
            # Log the message for debugging purposes
            logger.info(f"Default Visiting message: {message}")
            return None

        # Extract workflow UUID either from the message or thread-local storage
        if isinstance(message, IOMessage):
            workflow_uuid = message.workflow_uuid
        else:
            # This is an unexpected case - log the error and fall back to thread-local value
            logger.error(f"Message is not an IOMessage: {message}")
            logger.error(f"Message type: {type(message)}")
            workflow_uuid = workflow_ids.workflow_uuid

        # Convert async function to synchronous call and return result
        return syncify(a_visit_default)(self, message, workflow_uuid)
    
    def visit_text_message(self, message: TextMessage) -> None:
        """Process a text message from the FastAgency framework.
        
        This method handles TextMessage objects from FastAgency and sends them 
        to the UI using a three-part event sequence: start, content, and end.
        Also updates state to reflect message processing and conversation status.
        
        Args:
            message (TextMessage): The message to process and display in the UI
        """
        async def a_visit_text_message(self: AGUIAdapter, message: TextMessage) -> None:
            # Step 1: Extract workflow ID and get thread info
            workflow_uuid = message.workflow_uuid
            thread_info = self.get_thread_info_of_workflow(workflow_uuid)
            if thread_info is None:
                logger.error(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )
                return
            out_queue = thread_info.out_queue

            # Step 2: Update state to show message processing
            processing_delta = [
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "processing_message"
                },
                {
                    "op": "replace",
                    "path": "/agent/current_task",
                    "value": "Processing message..."
                }
            ]
            state_delta = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=processing_delta
            )
            out_queue.put_nowait(state_delta)

            # Step 3: Send the message start event
            message_started = TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message.uuid,
                role="assistant",
            )
            out_queue.put_nowait(message_started)

            # Step 4: Send the message content event
            message_content = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message.uuid,
                delta=message.body,
            )
            out_queue.put_nowait(message_content)

            # Step 5: Send the message end event
            message_end = TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END, message_id=message.uuid
            )
            out_queue.put_nowait(message_end)

            # Step 6: Update state to show message complete
            completion_delta = [
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "message_complete"
                },
                {
                    "op": "replace",
                    "path": "/agent/current_task",
                    "value": None
                },
                {
                    "op": "add",
                    "path": "/conversation/messages/-",
                    "value": {
                        "id": message.uuid,
                        "role": "assistant",
                        "content": message.body,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            ]
            state_delta = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=completion_delta
            )
            out_queue.put_nowait(state_delta)

        # Convert the async function to synchronous and execute it
        syncify(a_visit_text_message)(self, message)
    
    def visit_text_input(self, message: TextInput) -> str:
        """Process a text input request from the FastAgency framework.
        
        This method handles prompting the user for input through the UI and then
        waiting for their response. It follows the pattern of:
        1. Display the prompt as a message
        2. Signal the end of the run to let the UI acquire input
        3. Wait for user's response
        4. Update state to reflect input status
        
        Args:
            message (TextInput): The input request message
            
        Returns:
            str: The user's response text, or empty string if they continued without input
            
        Raises:
            KeyError: If the associated thread cannot be found
        """
        async def a_visit_text_input(self: AGUIAdapter, message: TextInput) -> str:
            # Step 1: Get the thread info for this workflow
            workflow_uuid = message.workflow_uuid
            thread_info = self.get_thread_info_of_workflow(workflow_uuid)
            if thread_info is None:
                logger.error(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )
                raise KeyError(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )

            # Step 2: Get the output queue for sending messages to the UI
            out_queue = thread_info.out_queue

            # Step 3: Update state to show input request
            input_request_delta = [
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "awaiting_input"
                },
                {
                    "op": "replace",
                    "path": "/agent/current_task",
                    "value": "Waiting for user input..."
                },
                {
                    "op": "replace",
                    "path": "/ui/showInput",
                    "value": True
                }
            ]
            state_delta = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=input_request_delta
            )
            out_queue.put_nowait(state_delta)

            # Step 4: Send the prompt message start
            message_started = TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message.uuid,
                role="assistant",
            )
            out_queue.put_nowait(message_started)

            # Step 5: Adjust the prompt text for UI display
            if message.prompt:
                prompt = message.prompt.replace(
                    "Press enter to skip and use auto-reply",
                    "Answer continue to skip and use auto-reply",
                )
            
            # Step 6: Send the prompt content
            message_content = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message.uuid,
                delta=prompt,
            )
            out_queue.put_nowait(message_content)

            # Step 7: Signal the end of the message
            message_end = TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END, message_id=message.uuid
            )
            out_queue.put_nowait(message_end)

            # Step 8: Check if the thread has a special widget for text input
            if thread_info.has_text_input_widget():
                # todo : invoke function to get an answer
                pass

            # Step 9: Update state to show input received before ending the run
            input_received_delta = [
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "input_received"
                },
                {
                    "op": "replace",
                    "path": "/ui/showInput",
                    "value": False
                },
                {
                    "op": "add",
                    "path": "/conversation/messages/-",
                    "value": {
                        "id": str(uuid4().hex),
                        "role": "user",
                        "content": "",  # Will be updated after getting response
                        "timestamp": datetime.now().isoformat()
                    }
                }
            ]
            state_delta = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=input_received_delta
            )
            out_queue.put_nowait(state_delta)

            # Step 10: Signal the end of the run so UI can acquire the answer
            run_finished = RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=thread_info.thread_id,
                run_id=thread_info.run_id,
            )
            out_queue.put_nowait(run_finished)

            # Step 11: Wait for user input from the UI
            response = await thread_info.input_queue.get()
            
            # Step 12: Process the response
            if response == "continue":
                response = ""
              # Check if messages array exists and has elements before updating
            # Get the current state to check message array
            current_state = thread_info.state
            conversation = current_state.get("conversation", {})
            messages = conversation.get("messages", [])
            
            if messages:
                # Messages array exists and has elements, update the last message
                message_update_delta = [
                    {
                        "op": "replace",
                        "path": "/conversation/messages/-1/content",
                        "value": response
                    }
                ]
            else:
                # Messages array is empty, add a new message instead
                message_update_delta = [
                    {
                        "op": "add",
                        "path": "/conversation/messages",
                        "value": [{
                            "id": str(uuid4().hex),
                            "role": "user",
                            "content": response,
                            "timestamp": datetime.now().isoformat()
                        }]
                    }
                ]
                
            state_delta = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=message_update_delta
            )
            out_queue.put_nowait(state_delta)
            
            return response

        # Convert async function to synchronous call and return result
        return syncify(a_visit_text_input)(self, message)

    # Non fastagency messages
    def visit_text(self, message: autogen.messages.agent_messages.TextMessage) -> None:
        """Handle text messages from AutoGen agents.
        
        This method processes TextMessage objects from the AutoGen framework and transforms
        them into the AG-UI event format. It follows a three-step process (start, content, end)
        to stream messages to the frontend.
        
        Args:
            message: An AutoGen text message containing content to be displayed in the UI
        """
        async def a_visit_text(
            self: AGUIAdapter,
            message: autogen.messages.agent_messages.TextMessage,
            workflow_uuid: str,
        ) -> None:
            # Log the incoming message for debugging purposes
            logger.info(f"Visiting text event: {message}")
            
            # Step 1: Retrieve the thread information associated with this workflow
            thread_info = self.get_thread_info_of_workflow(workflow_uuid)
            if thread_info is None:
                # If thread info is missing, log an error and abort processing
                logger.error(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )
                return

            # Step 2: Get the output queue for sending messages to the frontend
            out_queue = thread_info.out_queue
            
            # Step 3: Extract message content and generate a unique ID
            content = message.content
            uuid = str(content.uuid)
            
            # Step 4: Process non-empty messages only
            if content.content:
                # Step 4.1: Signal the start of a message from the assistant
                message_started = TextMessageStartEvent(
                    type=EventType.TEXT_MESSAGE_START, message_id=uuid, role="assistant"
                )
                out_queue.put_nowait(message_started)

                # Step 4.2: Send the actual message content
                message_content = TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=uuid,
                    delta=content.content,
                )
                out_queue.put_nowait(message_content)

                # Step 4.3: Signal the end of the message
                message_end = TextMessageEndEvent(
                    type=EventType.TEXT_MESSAGE_END, message_id=uuid
                )
                out_queue.put_nowait(message_end)

        # Get the current workflow UUID from thread-local storage
        workflow_uuid = workflow_ids.workflow_uuid
        
        # Execute the async function synchronously
        syncify(a_visit_text)(self, message, workflow_uuid)
    
    def visit_tool_call(
        self, message: autogen.messages.agent_messages.ToolCallMessage
    ) -> None:
        """Handle tool call messages from AutoGen agents.
        
        This method processes tool call requests from agents and notifies the UI
        about the tool being called. It follows a three-event sequence pattern and
        also displays an informational message about the tool call in the chat UI.
        Updates state to reflect tool execution status.
        
        Args:
            message: An AutoGen tool call message
        """
        async def a_visit_tool_call(
            self: AGUIAdapter,
            message: autogen.messages.agent_messages.ToolCallMessage,
            workflow_uuid: str,
        ) -> None:
            # Step 1: Log the incoming tool call and retrieve workflow information
            logger.info(f"Visiting tool call event: {message}")
            thread_info = self.get_thread_info_of_workflow(workflow_uuid)
            if thread_info is None:
                logger.error(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )
                return

            # Step 2: Prepare for sending messages to the UI
            out_queue = thread_info.out_queue
            content = message.content
            uuid = str(content.uuid)
            tool_name = content.tool_calls[0].function.name
            
            # Step 3: Update state to show tool execution starting
            tool_start_delta = [
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "executing"
                },
                {
                    "op": "replace",
                    "path": "/agent/current_task",
                    "value": f"Executing tool: {tool_name}"
                },
                {
                    "op": "replace",
                    "path": "/ui/showProgress",
                    "value": True
                }
            ]
            state_delta = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=tool_start_delta
            )
            out_queue.put_nowait(state_delta)
            
            # Step 4: Send a sequence of events for the tool call
            # Step 4.1: Signal the beginning of a tool call
            tool_call_id = f"call_{str(uuid4())[:8]}"
            tool_call_start = ToolCallStartEvent(
                message_id=uuid,
                toolCallId=tool_call_id,
                toolCallName=tool_name,
                tool=tool_name,
                delta=""
            )            
            out_queue.put_nowait(tool_call_start)
            
            # Step 4.2: Send the tool call arguments
            # Parse the JSON string into a Python dictionary
            import json
            args_dict = json.loads(content.tool_calls[0].function.arguments)
            
            tool_call_args = ToolCallArgsEvent(
                message_id=uuid,
                toolCallId=tool_call_id,
                toolCallName=tool_name,
                args=args_dict,  # Now it's a dictionary instead of a string
                delta=""
            )
            out_queue.put_nowait(tool_call_args)
            
            # Step 4.3: Mark the completion of the tool call
            tool_call_end = ToolCallEndEvent(
                message_id=uuid,
                toolCallId=tool_call_id,
                toolCallName=tool_name,
                delta=""
            )
            out_queue.put_nowait(tool_call_end)
            
            # input_queue = thread_info.input_queue
            # response = await input_queue.get()
            # if response == "continue":
            #     response = ""
            # message.content.respond(response)
            
            # Get the current state to check if tools array exists
            current_state = thread_info.state
            conversation = current_state.get("conversation", {})
            
            # Create the tool completion delta operations
            tool_complete_delta = [
                {
                    "op": "replace",
                    "path": "/status/phase",
                    "value": "tool_complete"
                },
                {
                    "op": "replace",
                    "path": "/agent/current_task",
                    "value": f"Completed tool: {tool_name}"
                },
                {
                    "op": "replace",
                    "path": "/ui/showProgress",
                    "value": False
                }
            ]
            
            # Check if tools array exists in the conversation object
            if "tools" in conversation:
                # Tools array exists, append to it
                tool_complete_delta.append({
                    "op": "add",
                    "path": "/conversation/tools/-",
                    "value": {
                        "id": uuid,
                        "name": tool_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "completed"
                    }
                })
            else:
                # Tools array doesn't exist, create it with the new tool
                tool_complete_delta.append({
                    "op": "add",
                    "path": "/conversation/tools",
                    "value": [{
                        "id": uuid,
                        "name": tool_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "completed"
                    }]
                })
                
            state_delta = StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=tool_complete_delta
            )
            out_queue.put_nowait(state_delta)
            
            # Step 6: Display a human-readable message about the tool call in the chat
            # message_started = TextMessageStartEvent(
            #     type=EventType.TEXT_MESSAGE_START, message_id=uuid + "_info", role="assistant"
            # )
            # out_queue.put_nowait(message_started)

            # message_content = TextMessageContentEvent(
            #     type=EventType.TEXT_MESSAGE_CONTENT,
            #     message_id=uuid + "_info",
            #     delta=f"The agent wants to invoke tool: {tool_name}",
            # )
            # out_queue.put_nowait(message_content)

            # message_end = TextMessageEndEvent(
            #     type=EventType.TEXT_MESSAGE_END, message_id=uuid + "_info"
            # )
            # out_queue.put_nowait(message_end)

        # Get workflow UUID from thread-local storage
        workflow_uuid = workflow_ids.workflow_uuid
        # Execute the async function synchronously
        syncify(a_visit_tool_call)(self, message, workflow_uuid)
    
    def visit_input_request(
        self, message: autogen.events.agent_events.InputRequestEvent
    ) -> None:
        """Handle input request events from AutoGen agents.
        
        This method processes requests for user input from AutoGen agents,
        displaying the prompt to the user and waiting for their response.
        The method follows the same pattern as visit_text_input but for AutoGen events.
        
        Args:
            message: The AutoGen input request event containing the prompt
        """
        async def a_visit_input_request(
            self: AGUIAdapter,
            message: autogen.events.agent_events.InputRequestEvent,
            workflow_uuid: str,
        ) -> None:
            # Step 1: Log the request and retrieve thread information
            logger.info(f"Visiting input request: {message}")
            thread_info = self.get_thread_info_of_workflow(workflow_uuid)
            if thread_info is None:
                logger.error(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )
                raise KeyError(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )

            # Step 2: Set up the output queue for UI messages
            out_queue = thread_info.out_queue
            
            # Step 3: Create a unique message ID for this input request
            uuid = str(uuid4().hex)
            
            # Step 4: Signal the start of an assistant message (the prompt)
            message_started = TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START, message_id=uuid, role="assistant"
            )
            out_queue.put_nowait(message_started)

            # Step 5: Modify the prompt for better UI presentation
            prompt = message.content.prompt.replace(
                "Press enter to skip and use auto-reply",
                "Answer continue to skip and use auto-reply",
            )

            # Step 6: Send the prompt content to the UI
            message_content = TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=uuid,
                delta="________________________________\n",
            )
            out_queue.put_nowait(message_content)

            # Step 7: Signal the end of the prompt message
            message_end = TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END, message_id=uuid
            )
            
            out_queue.put_nowait(message_end)
            
            # Step 8: Signal the end of the run so UI can acquire the user's response
            run_finished = RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=thread_info.thread_id,
                run_id=thread_info.run_id,
            )
            out_queue.put_nowait(run_finished)
            
            # Step 9: Wait for user input from the UI            

            input_queue = thread_info.input_queue
            response = await input_queue.get()
            if response == "continue":
                response = ""
            message.content.respond(response)

        workflow_uuid = workflow_ids.workflow_uuid
        syncify(a_visit_input_request)(self, message, workflow_uuid)

    def visit_run_completion(
        self, message: autogen.events.agent_events.RunCompletionEvent
    ) -> None:
        async def a_visit_run_completion(
            self: AGUIAdapter,
            message: autogen.events.agent_events.RunCompletionEvent,
            workflow_uuid: str,
        ) -> None:
            logger.info(f"Visiting run completion: {message}")
            thread_info = self.get_thread_info_of_workflow(workflow_uuid)
            if thread_info is None:
                logger.error(
                    f"Thread info not found for workflow {workflow_uuid}: {self._agui_threads}"
                )
                return
            out_queue = thread_info.out_queue

            # Start a new run for the completion state updates
            new_run_id = str(uuid4().hex)
            run_started = RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=thread_info.thread_id,
                run_id=new_run_id,
            )
            out_queue.put_nowait(run_started)

            # Send thread over event
            thread_over = CustomEvent(
                type=EventType.CUSTOM, name="thread_over", value={}
            )
            out_queue.put_nowait(thread_over)

            # End the new run
            run_finished = RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=thread_info.thread_id,
                run_id=new_run_id,
            )
            out_queue.put_nowait(run_finished)

        workflow_uuid = workflow_ids.workflow_uuid
        return syncify(a_visit_run_completion)(self, message, workflow_uuid)
    
    def handle_state_delta(self, delta: dict, thread_id: str) -> None:
        """Update state incrementally with a delta using JSON Patch operations.
        
        This method sends a StateDeltaEvent to update specific parts of the frontend state
        using JSON Patch operations (RFC 6902). This is more efficient than sending
        complete state snapshots when only small changes are needed.
        
        Args:
            delta (dict): The JSON Patch operations to apply to the state
            thread_id (str): The thread ID to send the update to
        """
        thread_info = self._agui_threads.get(thread_id)
        if not thread_info:
            logger.error(f"Thread {thread_id} not found")
            return
            
        # Update local state
        thread_info.update_state(delta)
        
        # Create and send state delta event
        state_delta = StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=delta
        )
        thread_info.out_queue.put_nowait(state_delta)
        
    def handle_state_snapshot(self, state: dict, thread_id: str) -> None:
        """Update state with a complete snapshot.
        
        This method sends a StateSnapshotEvent to replace the entire frontend state.
        Use this when many state changes need to be applied at once or when
        initializing the state for a new thread.
        
        Args:
            state (dict): The complete state object to replace current state
            thread_id (str): The thread ID to send the update to
        """
        thread_info = self._agui_threads.get(thread_id)
        if not thread_info:
            logger.error(f"Thread {thread_id} not found")
            return
            
        # Update local state
        thread_info.state = state.copy()
        
        # Create and send state snapshot event
        state_snapshot = StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            snapshot=state
        )
        thread_info.out_queue.put_nowait(state_snapshot)
        
    def handle_step_started(self, step_name: str, thread_id: str) -> None:
        """Handle step started event.
        
        Args:
            step_name (str): Name of the step
            thread_id (str): The thread ID
        """
        thread_info = self._agui_threads.get(thread_id)
        if not thread_info:
            logger.error(f"Thread {thread_id} not found")
            return
            
        step_started = CustomEvent(
            type=EventType.CUSTOM,
            name="STEP_STARTED",
            value={"stepName": step_name}
        )
        thread_info.out_queue.put_nowait(step_started)
        
    def handle_step_finished(self, step_name: str, thread_id: str) -> None:
        """Handle step finished event.
        
        Args:
            step_name (str): Name of the step
            thread_id (str): The thread ID
        """
        thread_info = self._agui_threads.get(thread_id)
        if not thread_info:
            logger.error(f"Thread {thread_id} not found")
            return
            
        step_finished = CustomEvent(
            type=EventType.CUSTOM,
            name="STEP_FINISHED",
            value={"stepName": step_name}
        )
        thread_info.out_queue.put_nowait(step_finished)

    def create_subconversation(self) -> UIBase:
        return self

    @contextmanager
    def create(self, app: Runnable, import_string: str) -> Iterator[None]:
        raise NotImplementedError("create")

    def start(
        self,
        *,
        app: "Runnable",
        import_string: str,
        name: Optional[str] = None,
        params: dict[str, Any],
        single_run: bool = False,
    ) -> None:
        raise NotImplementedError("start")

    @classmethod
    def create_provider(
        cls,
        fastapi_url: str,
    ) -> ProviderProtocol:
        raise NotImplementedError("create")


logger = get_logger(__name__)
