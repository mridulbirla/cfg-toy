import gradio as gr
import requests
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = "http://localhost:8000"

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

def generate_query(natural_language_query):
    """Generate ClickHouse query from natural language"""
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

def run_evaluation():
    """Run evaluation tests with progress tracking"""
    try:
        response = requests.post(f"{API_BASE_URL}/evaluate-stream", timeout=120, stream=True)
        response.raise_for_status()
        
        # Process streaming response
        progress_text = "## Evaluation Progress\n\n"
        final_results = None
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                        
                        if data['type'] == 'start':
                            progress_text += f"🚀 {data['message']}\n\n"
                        elif data['type'] == 'progress':
                            progress_text += f"**Test {data['current']}/{data['total']}** ({data['progress_percent']:.1f}%)\n"
                            progress_text += f"- {data['description']} - {data['status']}\n\n"
                        elif data['type'] == 'complete':
                            final_results = data['results']
                        elif data['type'] == 'error':
                            return f"❌ Error: {data['message']}"
                            
                    except json.JSONDecodeError:
                        continue
        
        if not final_results:
            return "❌ No results received"
        
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
        
        return summary + details
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return f"Error: {str(e)}"

def check_health():
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

def update_config(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database, openai_api_key):
    """Update application configuration"""
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

def test_clickhouse_connection(clickhouse_host, clickhouse_port, clickhouse_username, clickhouse_password, clickhouse_database):
    """Test ClickHouse connection"""
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

def test_openai_connection(openai_api_key):
    """Test OpenAI connection"""
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

# Create Gradio interface
with gr.Blocks(title="CFG + Eval Toy", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧠 CFG + Eval Toy")
    gr.Markdown("Generate ClickHouse queries from natural language using GPT-5's Context Free Grammar")
    
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
                
                # Use regular evaluation for now (streaming can be added later)
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
