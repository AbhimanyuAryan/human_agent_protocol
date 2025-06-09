# AG-UI + AutoGen Integration

This project demonstrates the integration of AutoGen agents with the AG-UI protocol for building interactive AI applications with human-in-the-loop capabilities.

## Overview

The integration showcases a travel agent built with AutoGen that communicates with frontend clients using the AG-UI protocol. The implementation follows event-driven architecture with Server-Sent Events (SSE) for real-time communication.

## Features

- **AutoGen Travel Agent**: Creates personalized travel itineraries based on user preferences
- **Human-in-the-Loop Workflow**: Supports tool calls that can be executed by humans
- **AG-UI Protocol**: Standardized communication between frontend and AI services
- **Real-time Streaming**: Character-by-character streaming of AI responses
- **Tool Execution**: Function calling with standardized protocol events

## Prerequisites

- Python 3.12+
- Poetry (for dependency management)
- OpenAI API key

## Setup

1. Clone the repository
2. Create a `.env` file with your API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Install dependencies:
   ```
   poetry install
   ```

## Running the Server

Start the FastAPI server:

```bash
python -m ag_ui_ag2.demo
```

This will start the server at `http://localhost:8000`.

## API Endpoints

### POST /travel-agent

AG-UI compliant endpoint for the travel agent.

**Request Format**:

```json
{
  "thread_id": "string",
  "run_id": "string",
  "messages": [
    {
      "id": "string",
      "content": "string",
      "role": "user"
    }
  ]
}
```

**Response**: Server-Sent Events (SSE) stream following the AG-UI protocol.

## Example Usage

The travel agent supports the following workflow:

1. User provides membership ID (try P12345, P67890, S12345, S67890)
2. Agent retrieves member information
3. User specifies destination and travel duration
4. Agent creates a personalized itinerary
5. User can review and request modifications

## Integration with Frontend Applications

This server can be integrated with any frontend application that implements the AG-UI client protocol, such as:

- Web applications with [AG-UI client library](https://www.npmjs.com/package/ag-ui)
- React applications with [CopilotKit](https://docs.copilotkit.ai)

## License

MIT
