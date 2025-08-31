import gradio as gr
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = "http://localhost:8000"

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
    """Run evaluation tests"""
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
        
        eval_results = gr.Markdown(label="Evaluation Results")
        
        eval_button.click(
            run_evaluation,
            outputs=[eval_results]
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
