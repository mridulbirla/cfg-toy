---
title: CFG + Eval Toy
emoji: 🧩
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "4.41.0"
app_file: gradio_app.py
pinned: false
---

# CFG + Eval Toy

A Python application that demonstrates GPT-5's new Context Free Grammar (CFG) capabilities for generating ClickHouse queries from natural language.

## Features

- **Natural Language to ClickHouse Query**: Convert natural language to structured ClickHouse SQL using GPT-5 CFG
- **Interactive Gradio Interface**: User-friendly web interface for testing queries
- **Evaluation Framework**: Built-in test cases to evaluate CFG accuracy
- **Real-time Query Execution**: Execute generated queries against ClickHouse database
- **Performance Metrics**: Track query generation time and accuracy

## Technology Stack

- **Backend**: Python with FastAPI
- **Frontend**: Gradio
- **AI**: OpenAI GPT-5 with CFG (Context Free Grammar)
- **Database**: ClickHouse
- **Grammar**: Lark syntax for CFG definition

## Quick Start

### 1. Prerequisites

- Python 3.8+
- OpenAI API key with GPT-5 access
- ClickHouse database (local or cloud)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/mridulbirla/cfg-toy
cd cfg-eval-toy

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (optional - can also use Gradio UI)
# Edit .env file with your API keys and database credentials
```

### 3. Configuration

You can configure the application in two ways:

#### Option A: Using the Gradio UI (Recommended)
1. Start the application: `python gradio_app.py`
2. Navigate to the "Configuration" tab
3. Enter your ClickHouse and OpenAI credentials
4. Test connections using the "Test" buttons
5. Click "Update Configuration" to save settings

#### Option B: Using Environment Variables
Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ClickHouse Configuration
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=your_password
CLICKHOUSE_DATABASE=default

# Application Configuration
DEBUG=False
PORT=8000
```

### 4. Running the Application

```bash
# Start the API server
python main.py

# In another terminal, start the Gradio interface
python gradio_app.py
```

The application will be available at:
- **Gradio UI**: http://localhost:7860
- **API**: http://localhost:8000

## Configuration Features

### Dynamic Configuration
- **No Restart Required**: Update credentials through the Gradio UI without restarting the application
- **Persistent Storage**: Configuration is automatically saved to `app_config.json`
- **Connection Testing**: Test ClickHouse and OpenAI connections before saving
- **Fallback Support**: Falls back to environment variables if no UI configuration is set

### Configuration Tab Features
- **ClickHouse Settings**: Host, port, username, password, database
- **OpenAI Settings**: API key configuration
- **Test Connections**: Verify credentials before saving
- **Real-time Updates**: Changes take effect immediately
