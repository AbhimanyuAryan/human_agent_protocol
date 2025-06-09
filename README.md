### Step 1: Set Up the Backend

```bash
cd ag-ui-travel-agent

# Create a .env file with your API key
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Install dependencies
poetry install

# Start the simple server
poetry run python -m ag_ui_ag2.simple_server
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

