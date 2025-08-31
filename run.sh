#!/bin/bash

# Activate virtual environment
source /Users/pallavimantri/personal_space/raindrop_env/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'ENVEOF'
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
ENVEOF
    echo "✅ Created .env file - please configure your API keys and database credentials"
    echo "⚠️  Please edit .env file before running the application"
    exit 1
fi

# Check if OpenAI API key is configured
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  Please configure your OpenAI API key in .env file"
    exit 1
fi

# Check if ClickHouse host is configured
if grep -q "your_clickhouse_host_here" .env; then
    echo "⚠️  Please configure your ClickHouse credentials in .env file"
    exit 1
fi

echo "🚀 Starting CFG + Eval Toy..."

# Check command line arguments
case "$1" in
    "backend")
        echo "�� Starting FastAPI backend..."
        python main.py
        ;;
    "frontend")
        echo "🎨 Starting Gradio frontend..."
        python gradio_app.py
        ;;
    "setup-db")
        echo "🗄️  Setting up database..."
        python -m database.setup_database
        ;;
    "eval")
        echo "🧪 Running evaluation..."
        python -c "from evaluation.evaluator import Evaluator; e = Evaluator(); print(e.run_evaluation())"
        ;;
    *)
        echo "Usage: $0 {backend|frontend|setup-db|eval}"
        echo ""
        echo "Commands:"
        echo "  backend    - Start FastAPI backend server"
        echo "  frontend   - Start Gradio frontend"
        echo "  setup-db   - Setup database with sample data"
        echo "  eval       - Run evaluation tests"
        echo ""
        echo "Example workflow:"
        echo "  1. $0 setup-db    # Setup database first"
        echo "  2. $0 backend     # Start backend in one terminal"
        echo "  3. $0 frontend    # Start frontend in another terminal"
        exit 1
        ;;
esac
