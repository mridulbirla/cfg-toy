import gradio as gr
import requests
import json
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if running in Hugging Face Spaces or other cloud environments
IS_HF_SPACES = (
    os.getenv("SPACE_ID") is not None or 
    os.getenv("HUGGINGFACE_SPACE_ID") is not None or
    os.getenv("GRADIO_SERVER_NAME") is not None or
    "huggingface" in os.getenv("HOSTNAME", "").lower()
)

# API configuration
if IS_HF_SPACES:
    # In Hugging Face Spaces, we'll use integrated backend
    API_BASE_URL = None
    logger.info("🌐 Detected Hugging Face Spaces environment - using integrated backend")
else:
    # Local development with separate API server
    API_BASE_URL = "http://localhost:8000"
    logger.info("🏠 Detected local environment - using API server")

# Global configuration storage
app_config = {
    "clickhouse": {
        "host": "localhost",
        "port": "8123",
        "username": "default",
        "password": "",
        "database": "default"
    },
    "openai": {
        "api_key": ""
    }
}

# Load configuration from file if it exists
CONFIG_FILE = "app_config.json"
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            saved_config = json.load(f)
            if "clickhouse" in saved_config:
                app_config["clickhouse"].update(saved_config["clickhouse"])
            if "openai" in saved_config:
                app_config["openai"].update(saved_config["openai"])
    except Exception as e:
        logger.warning(f"Could not load config file: {e}")

# Import backend components for integrated mode
if IS_HF_SPACES:
    try:
        # Add the current directory to Python path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        logger.info("🔄 Attempting to load integrated backend components...")
        
        # Try to import each component individually with detailed error reporting
        try:
            from config import Config
            logger.info("✅ Config module loaded")
        except Exception as e:
            logger.error(f"❌ Failed to import config: {e}")
            raise
        
        try:
            from database.clickhouse_client import ClickHouseClient
            logger.info("✅ ClickHouseClient module loaded")
        except Exception as e:
            logger.error(f"❌ Failed to import ClickHouseClient: {e}")
            raise
        
        try:
            from cfg.query_generator import QueryGenerator
            logger.info("✅ QueryGenerator module loaded")
        except Exception as e:
            logger.error(f"❌ Failed to import QueryGenerator: {e}")
            raise
        
        try:
            from evaluation.evaluator import Evaluator
            logger.info("✅ Evaluator module loaded")
        except Exception as e:
            logger.error(f"❌ Failed to import Evaluator: {e}")
            raise
        
        # Initialize components with error handling
        try:
            Config.load_config_from_file()
            logger.info("✅ Config loaded from file")
        except Exception as e:
            logger.warning(f"⚠️ Could not load config from file: {e}")
        
        try:
            db_client = ClickHouseClient()
            logger.info("✅ ClickHouseClient initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ClickHouseClient: {e}")
            raise
        
        try:
            query_generator = QueryGenerator()
            logger.info("✅ QueryGenerator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize QueryGenerator: {e}")
            raise
        
        try:
            evaluator = Evaluator()
            logger.info("✅ Evaluator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Evaluator: {e}")
            raise
        
        logger.info("✅ All integrated backend components loaded successfully")
        
        # Test if components are actually working
        try:
            # Test ClickHouse client
            test_result = db_client.test_connection_with_config({"clickhouse": {"host": "test"}})
            logger.info(f"✅ ClickHouse client test: {test_result}")
            
            # Test QueryGenerator
            test_result = query_generator.test_connection_with_config({"openai": {"api_key": "test"}})
            logger.info(f"✅ QueryGenerator test: {test_result}")
            
            INTEGRATED_MODE = True
            logger.info("✅ All components tested and working")
            
        except Exception as test_e:
            logger.error(f"❌ Component test failed: {test_e}")
            raise test_e
        
    except Exception as e:
        logger.error(f"❌ Failed to load integrated backend: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error details: {str(e)}")
        
        # Don't create minimal components - let it fail completely
        logger.error("❌ Integrated backend failed to load - no fallback")
        INTEGRATED_MODE = False
else:
    INTEGRATED_MODE = False

def generate_query_integrated(natural_language_query):
    """Generate ClickHouse query using integrated backend"""
    try:
        # Generate query using GPT-5 CFG
        response = query_generator.generate_query(natural_language_query)
        
        # Check if we need clarification
        if response["status"] == "needs_clarification":
            clarification = response.get("clarification", "I need more information to generate the query.")
            return (
                f"🤔 Clarification needed:\n\n{clarification}",
                "No results - clarification needed",
                "N/A"
            )
        
        # Execute query if we have one
        if response["query"]:
            result = db_client.execute_query(response["query"])
            return (
                response["query"],
                json.dumps(result, indent=2),
                f"{result['execution_time']:.2f}ms"
            )
        else:
            return (
                f"❌ Error: {response.get('clarification', 'Unknown error')}",
                "No results - error occurred",
                "N/A"
            )
        
    except Exception as e:
        logger.error(f"Query generation failed: {e}")
        return f"Error: {str(e)}", "", ""

def generate_query_api(natural_language_query):
    """Generate ClickHouse query using API server"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"natural_language_query": natural_language_query},
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Handle different response types
        if result["status"] == "needs_clarification":
            clarification = result.get("clarification", "I need more information to generate the query.")
            return (
                f"🤔 Clarification needed:\n\n{clarification}",
                "No results - clarification needed",
                "N/A"
            )
        elif result["status"] == "success":
            return (
                result["generated_query"],
                json.dumps(result["results"], indent=2),
                f"{result['execution_time']:.2f}ms"
            )
        else:
            return (
                f"❌ Error: {result.get('clarification', 'Unknown error')}",
                "No results - error occurred",
                "N/A"
            )
    except Exception as e:
        logger.error(f"Query generation failed: {e}")
        return f"Error: {str(e)}", "", ""

def generate_query(natural_language_query):
    """Generate ClickHouse query from natural language"""
    if INTEGRATED_MODE:
        return generate_query_integrated(natural_language_query)
    else:
        return generate_query_api(natural_language_query)

def run_evaluation_integrated():
    """Run evaluation using integrated backend"""
    try:
        evaluation_results = evaluator.run_evaluation()
        
        # Format final results
        metrics = evaluation_results["metrics"]
        summary = f"""
## Evaluation Results

**Overall Accuracy**: {metrics['accuracy']:.1%}
**Tests Passed**: {metrics['passed_tests']}/{metrics['total_tests']}
**Average Execution Time**: {metrics['average_execution_time']:.2f}ms

### Category Breakdown:
"""
        
        for category, stats in metrics['category_breakdown'].items():
            if stats['total'] > 0:
                summary += f"- **{category.title()}**: {stats['passed']}/{stats['total']} ({stats['accuracy']:.1%})\n"
        
        # Detailed results
        details = "\n### Detailed Results:\n"
        for test_result in evaluation_results["results"]:
            status = "✅ PASS" if test_result["is_correct"] else "❌ FAIL"
            details += f"\n**{status}** - {test_result['test_case']['description']}\n"
            details += f"- Expected: `{test_result['expected_query']}`\n"
            details += f"- Generated: `{test_result['generated_query']}`\n"
            if test_result.get('error'):
                details += f"- Error: {test_result['error']}\n"
        
        return summary + details
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return f"Error: {str(e)}"

def run_evaluation_api():
    """Run evaluation using API server"""
    try:
        response = requests.post(f"{API_BASE_URL}/evaluate", timeout=120)
        response.raise_for_status()
        
        result = response.json()
        metrics = result["metrics"]
        
        # Format results
        summary = f"""
## Evaluation Results

**Overall Accuracy**: {metrics['accuracy']:.1%}
**Tests Passed**: {metrics['passed_tests']}/{metrics['total_tests']}
**Average Execution Time**: {metrics['average_execution_time']:.2f}ms

### Category Breakdown:
"""
        
        for category, stats in metrics['category_breakdown'].items():
            if stats['total'] > 0:
                summary += f"- **{category.title()}**: {stats['passed']}/{stats['total']} ({stats['accuracy']:.1%})\n"
        
        # Detailed results
        details = "### Detailed Results:\n"
        for test_result in result["results"]:
            status = "✅ PASS" if test_result["is_correct"] else "❌ FAIL"
            details += f"\n**{status}** - {test_result['test_case']['description']}\n"
            details += f"- Expected: `{test_result['expected_query']}`\n"
            details += f"- Generated: `{test_result['generated_query']}`\n"
            if test_result.get('error'):
                details += f"- Error: {test_result['error']}\n"
        
        return summary + details
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return f"Error: {str(e)}"

def run_evaluation():
    """Run evaluation tests with progress tracking"""
    if INTEGRATED_MODE:
        return run_evaluation_integrated()
    else:
        return run_evaluation_api()

def check_health_integrated():
    """Check system health using integrated backend"""
    try:
        is_connected = db_client.test_connection()
        status = "🟢 Healthy" if is_connected else "🔴 Unhealthy"
        db_status = "🟢 Connected" if is_connected else "🔴 Disconnected"
        
        return f"""
## System Status

**API Status**: {status}
**Database**: {db_status}
**Mode**: Integrated Backend
**Timestamp**: {time.time()}
"""
    except Exception as e:
        return f"🔴 Error: {str(e)}"

def check_health_api():
    """Check API health"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        
        result = response.json()
        status = "🟢 Healthy" if result["status"] == "healthy" else "🔴 Unhealthy"
        db_status = "🟢 Connected" if result["database_connected"] else "🔴 Disconnected"
        
        return f"""
## System Status

**API Status**: {status}
**Database**: {db_status}
**Timestamp**: {result.get('timestamp', 'N/A')}
"""
    except Exception as e:
        return f"🔴 Error: {str(e)}"

def check_health():
    """Check system health"""
    if INTEGRATED_MODE:
        return check_health_integrated()
    else:
        return check_health_api()

def update_config_integrated(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database, openai_api_key):
    """Update application configuration using integrated backend"""
    global app_config
    
    # Update configuration
    app_config["clickhouse"] = {
        "host": clickhouse_host,
        "port": clickhouse_port,
        "username": clickhouse_username,
        "password": clickhouse_password,
        "database": clickhouse_database
    }
    app_config["openai"] = {
        "api_key": openai_api_key
    }
    
    try:
        # Update configuration in integrated backend
        Config.update_config(app_config)
        
        # Reconnect clients with new configuration
        if "clickhouse" in app_config:
            db_client.reconnect()
        if "openai" in app_config:
            query_generator.reconnect()
        
        return "✅ Configuration updated successfully!"
    except Exception as e:
        logger.error(f"Configuration update failed: {e}")
        return f"❌ Error updating configuration: {str(e)}"

def update_config_api(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database, openai_api_key):
    """Update application configuration using API"""
    global app_config
    
    # Update configuration
    app_config["clickhouse"] = {
        "host": clickhouse_host,
        "port": clickhouse_port,
        "username": clickhouse_username,
        "password": clickhouse_password,
        "database": clickhouse_database
    }
    app_config["openai"] = {
        "api_key": openai_api_key
    }
    
    try:
        # Send configuration to API
        response = requests.post(
            f"{API_BASE_URL}/config",
            json=app_config,
            timeout=10
        )
        response.raise_for_status()
        
        return "✅ Configuration updated successfully!"
    except Exception as e:
        logger.error(f"Configuration update failed: {e}")
        return f"❌ Error updating configuration: {str(e)}"

def update_config(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database, openai_api_key):
    """Update application configuration"""
    if INTEGRATED_MODE:
        return update_config_integrated(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database, openai_api_key)
    else:
        return update_config_api(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database, openai_api_key)

def test_clickhouse_connection_integrated(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database):
    """Test ClickHouse connection using integrated backend"""
    try:
        # Check if we have the real db_client (not minimal)
        if hasattr(db_client, 'test_connection_with_config'):
            # Check if it's the minimal version by looking for the specific error message
            test_result = db_client.test_connection_with_config({})
            if "Minimal mode" in str(test_result):
                return "🔴 Full backend not available - running in minimal mode. Check logs for import errors."
        
        test_config = {
            "clickhouse": {
                "host": clickhouse_host,
                "port": clickhouse_port,
                "username": clickhouse_username,
                "password": clickhouse_password,
                "database": clickhouse_database
            }
        }
        
        connected, error = db_client.test_connection_with_config(test_config)
        if connected:
            return "🟢 ClickHouse connection successful!"
        else:
            return f"🔴 ClickHouse connection failed: {error or 'Unknown error'}"
    except Exception as e:
        logger.error(f"ClickHouse test failed: {e}")
        return f"🔴 Error testing ClickHouse: {str(e)}"

def test_clickhouse_connection_api(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database):
    """Test ClickHouse connection using API"""
    try:
        test_config = {
            "clickhouse": {
                "host": clickhouse_host,
                "port": clickhouse_port,
                "username": clickhouse_username,
                "password": clickhouse_password,
                "database": clickhouse_database
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/test-clickhouse",
            json=test_config,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        if result["connected"]:
            return "🟢 ClickHouse connection successful!"
        else:
            return f"🔴 ClickHouse connection failed: {result.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"ClickHouse test failed: {e}")
        return f"🔴 Error testing ClickHouse: {str(e)}"

def test_clickhouse_connection(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database):
    """Test ClickHouse connection"""
    if INTEGRATED_MODE:
        return test_clickhouse_connection_integrated(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database)
    else:
        return test_clickhouse_connection_api(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database)

def test_openai_connection_integrated(openai_api_key):
    """Test OpenAI connection using integrated backend"""
    try:
        if not INTEGRATED_MODE or 'query_generator' not in globals():
            return "🔴 Integrated backend not available. Please check the logs."
        
        test_config = {
            "openai": {
                "api_key": openai_api_key
            }
        }
        
        connected, error = query_generator.test_connection_with_config(test_config)
        if connected:
            return "🟢 OpenAI connection successful!"
        else:
            return f"🔴 OpenAI connection failed: {error or 'Unknown error'}"
    except Exception as e:
        logger.error(f"OpenAI test failed: {e}")
        return f"🔴 Error testing OpenAI: {str(e)}"

def test_openai_connection_api(openai_api_key):
    """Test OpenAI connection using API"""
    try:
        test_config = {
            "openai": {
                "api_key": openai_api_key
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/test-openai",
            json=test_config,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        if result["connected"]:
            return "🟢 OpenAI connection successful!"
        else:
            return f"🔴 OpenAI connection failed: {result.get('error', 'Unknown error')}"
    except Exception as e:
        logger.error(f"OpenAI test failed: {e}")
        return f"🔴 Error testing OpenAI: {str(e)}"

def test_openai_connection(openai_api_key):
    """Test OpenAI connection"""
    if INTEGRATED_MODE:
        return test_openai_connection_integrated(openai_api_key)
    else:
        return test_openai_connection_api(openai_api_key)

# Create Gradio interface
with gr.Blocks(title="CFG + Eval Toy", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧠 CFG + Eval Toy")
    gr.Markdown("Generate ClickHouse queries from natural language using GPT-5's Context Free Grammar")
    
    # Show current mode and debug info
    mode_text = "🌐 **Integrated Mode** (Hugging Face Spaces)" if INTEGRATED_MODE else "🏠 **API Mode** (Local Development)"
    
    # Check if components are available
    components_status = []
    if INTEGRATED_MODE:
        components_status.append(f"- Config: {'✅' if 'Config' in globals() else '❌'}")
        components_status.append(f"- ClickHouseClient: {'✅' if 'db_client' in globals() else '❌'}")
        components_status.append(f"- QueryGenerator: {'✅' if 'query_generator' in globals() else '❌'}")
        components_status.append(f"- Evaluator: {'✅' if 'evaluator' in globals() else '❌'}")
        
        # Test if components are real or minimal
        if 'db_client' in globals():
            try:
                test_result = db_client.test_connection_with_config({})
                if "Minimal mode" in str(test_result):
                    components_status.append("- Backend Type: ❌ Minimal (fallback)")
                else:
                    components_status.append("- Backend Type: ✅ Full (real components)")
            except:
                components_status.append("- Backend Type: ❓ Unknown")
    
    # Check for required files
    required_files = [
        "config.py",
        "database/clickhouse_client.py", 
        "cfg/query_generator.py",
        "evaluation/evaluator.py",
        "cfg/grammar.py",
        "evaluation/test_cases.py"
    ]
    
    file_status = []
    for file_path in required_files:
        exists = os.path.exists(file_path)
        file_status.append(f"- {file_path}: {'✅' if exists else '❌'}")
    
    # Check Python path
    python_path_info = f"- Current directory: {os.getcwd()}"
    python_path_info += f"\n- Script directory: {os.path.dirname(os.path.abspath(__file__))}"
    python_path_info += f"\n- Python path entries: {len(sys.path)}"
    
    debug_info = f"""
**Current Mode**: {mode_text}
**Environment Variables**: 
- SPACE_ID: {os.getenv('SPACE_ID', 'Not set')}
- HOSTNAME: {os.getenv('HOSTNAME', 'Not set')}
- API_BASE_URL: {API_BASE_URL}
- INTEGRATED_MODE: {INTEGRATED_MODE}
- IS_HF_SPACES: {IS_HF_SPACES}

**Component Status**:
{chr(10).join(components_status) if components_status else '- No components loaded'}

**Required Files**:
{chr(10).join(file_status)}

**Python Path Info**:
{python_path_info}
"""
    gr.Markdown(debug_info)
    
    with gr.Tab("Query Interface"):
        with gr.Row():
            with gr.Column():
                query_input = gr.Textbox(
                    label="Natural Language Query",
                    placeholder="e.g., sum the total of all orders placed in the last 30 hours",
                    lines=3
                )
                query_button = gr.Button("Generate Query", variant="primary")
            
            with gr.Column():
                generated_query = gr.Code(
                    label="Generated ClickHouse Query",
                    language="sql",
                    interactive=False
                )
                results_json = gr.Code(
                    label="Query Results",
                    language="json",
                    interactive=False
                )
                execution_time = gr.Textbox(
                    label="Execution Time",
                    interactive=False
                )
        
        query_button.click(
            generate_query,
            inputs=[query_input],
            outputs=[generated_query, results_json, execution_time]
        )
    
    with gr.Tab("Evaluation"):
        with gr.Row():
            eval_button = gr.Button("Run Evaluation", variant="primary", size="lg")
        
        # Status text
        eval_status = gr.Markdown("Ready to run evaluation...")
        
        # Results
        eval_results = gr.Markdown(label="Evaluation Results")
        
        def run_evaluation_with_progress(progress=gr.Progress()):
            """Run evaluation with progress updates"""
            try:
                # Start with progress message
                progress_text = "## Evaluation Progress\n\n🚀 Starting evaluation...\n\n"
                yield progress_text, "🔄 Initializing..."
                
                if INTEGRATED_MODE:
                    # Use integrated backend
                    final_results = evaluator.run_evaluation()
                else:
                    # Use API server
                    response = requests.post(f"{API_BASE_URL}/evaluate", timeout=120)
                    response.raise_for_status()
                    final_results = response.json()
                
                # Simulate progress updates
                total_tests = len(final_results["results"])
                progress_text = "## Evaluation Progress\n\n🚀 Starting evaluation...\n\n📊 Running evaluation...\n\n"
                yield progress_text, f"🧪 Testing {total_tests} cases..."
                
                # Update progress bar
                progress(0.5, desc="Processing results...")
                
                progress_text = "## Evaluation Progress\n\n🚀 Starting evaluation...\n\n📊 Running evaluation...\n\n✅ Evaluation completed!\n\n"
                yield progress_text, "📊 Analyzing results..."
                
                # Format final results
                metrics = final_results["metrics"]
                summary = f"""
## Evaluation Results

**Overall Accuracy**: {metrics['accuracy']:.1%}
**Tests Passed**: {metrics['passed_tests']}/{metrics['total_tests']}
**Average Execution Time**: {metrics['average_execution_time']:.2f}ms

### Category Breakdown:
"""
                
                for category, stats in metrics['category_breakdown'].items():
                    if stats['total'] > 0:
                        summary += f"- **{category.title()}**: {stats['passed']}/{stats['total']} ({stats['accuracy']:.1%})\n"
                
                # Detailed results
                details = "\n### Detailed Results:\n"
                for test_result in final_results["results"]:
                    status = "✅ PASS" if test_result["is_correct"] else "❌ FAIL"
                    details += f"\n**{status}** - {test_result['test_case']['description']}\n"
                    details += f"- Expected: `{test_result['expected_query']}`\n"
                    details += f"- Generated: `{test_result['generated_query']}`\n"
                    if test_result.get('error'):
                        details += f"- Error: {test_result['error']}\n"
                
                # Final result with progress history
                final_text = f"""
## Evaluation Progress

🚀 Starting evaluation...
📊 Running evaluation...
✅ Evaluation completed!

{summary + details}
"""
                yield final_text, "✅ Complete!"
                
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
                yield f"Error: {str(e)}", "❌ Failed"
        
        eval_button.click(
            run_evaluation_with_progress,
            outputs=[eval_status, eval_results]
        )
    
    with gr.Tab("Configuration"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ClickHouse Configuration")
                clickhouse_host = gr.Textbox(
                    label="Host",
                    value=app_config["clickhouse"]["host"],
                    placeholder="localhost"
                )
                clickhouse_port = gr.Textbox(
                    label="Port",
                    value=app_config["clickhouse"]["port"],
                    placeholder="8123"
                )
                clickhouse_username = gr.Textbox(
                    label="Username",
                    value=app_config["clickhouse"]["username"],
                    placeholder="default"
                )
                clickhouse_password = gr.Textbox(
                    label="Password",
                    value=app_config["clickhouse"]["password"],
                    type="password"
                )
                clickhouse_database = gr.Textbox(
                    label="Database",
                    value=app_config["clickhouse"]["database"],
                    placeholder="default"
                )
                
                gr.Markdown("### OpenAI Configuration")
                openai_api_key = gr.Textbox(
                    label="API Key",
                    value=app_config["openai"]["api_key"],
                    type="password",
                    placeholder="sk-..."
                )
            
            with gr.Column():
                gr.Markdown("### Actions")
                test_clickhouse_btn = gr.Button("Test ClickHouse Connection", variant="secondary")
                test_openai_btn = gr.Button("Test OpenAI Connection", variant="secondary")
                update_config_btn = gr.Button("Update Configuration", variant="primary")
                
                config_status = gr.Markdown(label="Configuration Status")
                clickhouse_test_status = gr.Markdown(label="ClickHouse Test Status")
                openai_test_status = gr.Markdown(label="OpenAI Test Status")
        
        # Event handlers
        test_clickhouse_btn.click(
            test_clickhouse_connection,
            inputs=[clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database],
            outputs=[clickhouse_test_status]
        )
        
        test_openai_btn.click(
            test_openai_connection,
            inputs=[openai_api_key],
            outputs=[openai_test_status]
        )
        
        update_config_btn.click(
            update_config,
            inputs=[clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database, openai_api_key],
            outputs=[config_status]
        )
    
    with gr.Tab("System Status"):
        with gr.Row():
            health_button = gr.Button("Check Health", variant="secondary")
        
        health_status = gr.Markdown(label="System Status")
        
        health_button.click(
            check_health,
            outputs=[health_status]
        )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
