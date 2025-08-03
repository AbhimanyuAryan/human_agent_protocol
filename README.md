## Example taken from here

https://docs.copilotkit.ai/ag2/quickstart

### Step 1: Set Up the Backend

```bash
cd ag-ui-travel-agent

# Create a .env file with your API key
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Install dependencies
poetry install

# Start the server
poetry run uvicorn src.ag_ui_ag2.hitl_workflow:app --host 0.0.0.0 --port 8000 --reload

# Start the server (macOS/Linux)
PYTHONPATH=src poetry run uvicorn agent_back.hitl_workflow:app --host 0.0.0.0 --port 8000 --reload
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
