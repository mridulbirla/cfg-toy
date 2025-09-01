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
```

### 3. Database Setup

```bash
# Setup database with sample data
python -m database.setup_database
```

### 4. Run the Application

```bash
# Start the FastAPI backend
python main.py

# In another terminal, start the Gradio frontend
python gradio_app.py
```

### 5. Access the Application

- **FastAPI Backend**: http://localhost:8000
- **Gradio UI**: http://localhost:7860
- **API Documentation**: http://localhost:8000/docs

## Usage

### Query Interface

1. Go to the "Query Interface" tab
2. Enter a natural language query like:
   - "sum the total of all orders placed in the last 30 hours"
   - "count orders with status completed"
   - "average order amount by status"
3. Click "Generate Query" to see the ClickHouse SQL and results

### Evaluation

1. Go to the "Evaluation" tab
2. Click "Run Evaluation" to test the CFG with predefined test cases
3. View accuracy metrics and detailed results

### System Status

1. Go to the "System Status" tab
2. Click "Check Health" to verify API and database connectivity

## API Endpoints

- `GET /health` - Health check
- `POST /query` - Generate and execute ClickHouse query
- `POST /evaluate` - Run evaluation tests

## CFG Grammar

The application uses a Lark-based grammar that constrains GPT-5 to generate valid ClickHouse queries:

```lark
start: select_statement SEMI

select_statement: SELECT SP select_list SP FROM SP table_name where_clause? group_clause? order_clause? limit_clause?

select_list: aggregate_function | column_list
aggregate_function: COUNT LPAREN ASTERISK RPAREN | aggregate_func_name LPAREN column_name RPAREN
```

## Test Cases

The evaluation framework includes 5 test cases covering:

1. **Basic**: Simple COUNT queries
2. **Aggregation**: SUM, AVG, MAX, MIN functions
3. **Filtering**: WHERE clauses with conditions
4. **Complex**: GROUP BY, ORDER BY operations

## Environment Variables

Create a `.env` file with:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ClickHouse Configuration
CLICKHOUSE_HOST=your_clickhouse_host_here
CLICKHOUSE_PORT=8123
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=your_clickhouse_password_here
CLICKHOUSE_DATABASE=default

# Application Configuration
DEBUG=False
PORT=8000
```

## Project Structure

```
cfg-eval-toy/
├── main.py                 # FastAPI application
├── gradio_app.py          # Gradio interface
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── setup.py              # Setup script
├── database/             # Database layer
│   ├── clickhouse_client.py
│   └── setup_database.py
├── cfg/                  # CFG implementation
│   ├── grammar.py
│   └── query_generator.py
├── evaluation/           # Evaluation framework
│   ├── test_cases.py
│   └── evaluator.py
└── utils/               # Utilities
```

## Development

### Running Tests

```bash
# Run evaluation tests
python -c "from evaluation.evaluator import Evaluator; e = Evaluator(); print(e.run_evaluation())"
```

### Adding New Test Cases

Edit `evaluation/test_cases.py` to add new test cases:

```python
{
    "id": "new-test",
    "natural_language_query": "your natural language query",
    "expected_query": "SELECT expected SQL query;",
    "description": "Test description",
    "category": "basic|aggregation|filtering|complex"
}
```

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Ensure you have GPT-5 access and valid API key
2. **ClickHouse Connection**: Verify database credentials and network connectivity
3. **Grammar Errors**: Check Lark grammar syntax in `cfg/grammar.py`

### Logs

The application uses Python logging. Check console output for detailed error messages.

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
