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

# Run setup script
python setup.py

# Configure environment variables
# Edit .env file with your API keys and database credentials
