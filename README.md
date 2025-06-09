# Simple Travel Assistant

A simplified full-stack application demonstrating AutoGen agents with a FastAPI backend and simple React frontend for creating an interactive AI travel assistant.

![Travel Assistant](https://img.shields.io/badge/AI-Travel%20Assistant-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)
![AutoGen](https://img.shields.io/badge/Framework-AutoGen-orange)
![React](https://img.shields.io/badge/Frontend-React-purple)

## 📋 Overview

This project showcases a simplified AI application architecture that combines:

1. **Backend**: Python-based AutoGen agents with FastAPI server
2. **Communication**: WebSocket for real-time messaging  
3. **Frontend**: Clean React application with pure CSS styling

The system allows users to interact with an AI travel assistant that can create custom travel plans, recommend destinations, and adjust itineraries based on user feedback - all with real-time messaging.

## 🌟 Features

### Backend (Travel Agent)
- **AutoGen-powered AI**: Leverages AutoGen's multi-agent architecture for sophisticated planning
- **Human-in-the-Loop**: Supports human execution of tool calls when needed
- **Member Data Integration**: Connects to member profiles for personalized recommendations
- **WebSocket Communication**: Real-time bi-directional communication
- **FastAPI Architecture**: Modern async Python web framework

### Frontend (Simple React App)
- **Pure React**: No complex dependencies, just React and CSS
- **Real-time Messaging**: WebSocket-based chat interface
- **Responsive Design**: Works across desktop and mobile devices
- **Connection Management**: Auto-reconnection and visual status indicators
- **Clean UI**: Modern, accessible interface with typing indicators

## 🔧 Prerequisites

- **Backend**:
  - Python 3.12+
  - Poetry (for dependency management)
  - OpenAI API key

- **Frontend**:
  - Node.js 16+
  - npm

## 🚀 Getting Started

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd AG-UI-AG2
```

### Step 2: Set Up the Backend

```bash
cd ag-ui-travel-agent

# Create a .env file with your API key
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Install dependencies
poetry install

# Start the server
poetry run uvicorn src.ag_ui_ag2.hitl_workflow:app --host 0.0.0.0 --port 8000 --reload
```

The backend server will start at `http://localhost:8000`.

### Step 3: Set Up the Frontend

```bash
cd ../simple-travel-frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`.

## 🧩 Project Structure

```
AG-UI-AG2/
├── ag-ui-travel-agent/           # Backend Python application
│   ├── src/
│   │   └── ag_ui_ag2/            # Core Python package
│   │       ├── __init__.py
│   │       ├── hitl_workflow.py  # Main FastAPI application
│   │       ├── ag_ui_adapter.py  # AG-UI protocol adapter
│   │       ├── tool_events.py    # Tool call event definitions
│   │       ├── events.py         # Event type definitions
│   │       ├── types.py          # Type definitions
│   │       ├── encoder.py        # Event encoding utilities
│   │       ├── database.py       # Member database simulation
│   │       └── messages.py       # Message templates
│   ├── poetry.lock
│   ├── pyproject.toml            # Python dependencies
│   └── README.md
│
└── simple-travel-frontend/       # Frontend React application
    ├── src/
    │   ├── App.js                # Main React component
    │   ├── App.css               # Component styling
    │   ├── index.js              # React entry point
    │   └── index.css             # Global styles
    ├── public/
    │   └── index.html            # HTML template
    ├── package.json              # Frontend dependencies
    └── README.md
```

## 💻 Usage Examples

### Travel Planning Workflow

1. **Start Conversation**:
   - Open the React frontend at http://localhost:3000
   - You'll see a welcome message explaining available features

2. **Member Identification**:
   - Enter member ID (sample IDs: P12345, P67890, S12345, S67890)
   - System retrieves personalized member information

3. **Destination Selection**:
   - Specify travel destination and dates
   - AI agent provides recommendations based on preferences

4. **Itinerary Creation**:
   - AI generates a custom travel itinerary
   - Review activities, accommodations, and transportation

5. **Refinement**:
   - Request changes to the itinerary
   - AI adjusts plans based on feedback

## 🔌 Communication Protocol

### WebSocket Messages

The frontend and backend communicate via WebSocket with simple JSON messages:

**Client to Server**:
```json
{
  "type": "user_message",
  "content": "I'd like to plan a trip to Paris"
}
```

**Server to Client**:
```json
{
  "type": "message",
  "data": {
    "id": "msg_123",
    "role": "assistant",
    "content": "I'd be happy to help you plan a trip to Paris!",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 🛠️ Advanced Configuration

### Backend Configuration

Environment variables can be set in the `.env` file:

```
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o-mini
```

### Frontend Configuration

The WebSocket connection URL can be modified in `App.js`:

```javascript
const wsUrl = `ws://localhost:8000/ws/${clientId.current}`;
```

## 📚 Technologies Used

### Backend
- **AutoGen**: Multi-agent framework for AI applications
- **FastAPI**: High-performance async API framework
- **WebSocket**: Real-time communication
- **Poetry**: Python dependency management
- **Pydantic**: Data validation and serialization

### Frontend
- **React**: Frontend library (Create React App)
- **WebSocket API**: Real-time communication
- **Pure CSS**: Clean, responsive styling
- **No external dependencies**: Minimal, lightweight approach

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

For questions or feedback, please open an issue on the repository.

---

Built with ❤️ using AutoGen, FastAPI, and React
