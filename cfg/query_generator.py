import openai
from config import Config
from .grammar import CLICKHOUSE_GRAMMAR
import logging

logger = logging.getLogger(__name__)

class QueryGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_query(self, natural_language_query: str):
        """Generate ClickHouse query from natural language using GPT-5 with CFG"""
        return self.generate_query_with_clarification(natural_language_query)
    
    def generate_query_with_clarification(self, natural_language_query: str):
        """Generate ClickHouse query from natural language using GPT-5 with CFG, returning clarification if needed"""
        try:
            # Make the prompt more conversational
            enhanced_prompt = f"""
Hey! I need you to help me convert this natural language question into a ClickHouse SQL query.

The user asked: "{natural_language_query}"

Could you use the clickhouse_grammar tool to generate the appropriate SQL query? If query is very ambiguous, you should return a clarification message.

Thanks!
"""
            
            response = self.client.responses.create(
                model="gpt-5",
                input=enhanced_prompt,
                text={"format": {"type": "text"}},
                tools=[
                    {
                        "type": "custom",
                        "name": "clickhouse_grammar",
                        "description": "Executes read-only ClickHouse queries limited to SELECT statements with basic WHERE/ORDER BY/GROUP BY/LIMIT. YOU MUST REASON HEAVILY ABOUT THE QUERY AND MAKE SURE IT OBEYS THE GRAMMAR.",
                        "format": {
                            "type": "grammar",
                            "syntax": "lark",
                            "definition": CLICKHOUSE_GRAMMAR
                        }
                    },
                ],
                parallel_tool_calls=False
            )
            
            # Extract the generated query from the response with robust handling
            generated_query = None
            clarification_message = None


            # Try different ways to extract the query
            for i, output in enumerate(response.output):
                logger.info(f"Checking output[{i}] type: {type(output)}")
                
                if hasattr(output, 'input') and output.input:
                    if isinstance(output.input, list):
                        generated_query = output.input[0].strip() if output.input else ""
                    else:
                        generated_query = output.input.strip()
                    logger.info(f"Found query in output[{i}].input: {generated_query}")
                    break
                elif hasattr(output, 'content') and output.content:
                    # Handle ResponseOutputText objects
                    if hasattr(output.content, 'text'):
                        content_text = output.content.text.strip()
                        # Check if this looks like a clarification message
                        if any(phrase in content_text.lower() for phrase in ['clarify', 'specify', 'could you', 'please', 'what do you want', 'not sure', 'infer']):
                            clarification_message = content_text
                            logger.info(f"Found clarification message: {clarification_message}")
                            return {
                                "query": None,
                                "clarification": clarification_message,
                                "status": "needs_clarification"
                            }
                        else:
                            generated_query = content_text
                            logger.info(f"Found query in output[{i}].content.text: {generated_query}")
                            break
                    elif isinstance(output.content, list):
                        if output.content and hasattr(output.content[0], 'text'):
                            content_text = output.content[0].text.strip()
                            # Check if this looks like a clarification message
                            if any(phrase in content_text.lower() for phrase in ['clarify', 'specify', 'could you', 'please', 'what do you want', 'not sure', 'infer']):
                                clarification_message = content_text
                                logger.info(f"Found clarification message: {clarification_message}")
                                return {
                                    "query": None,
                                    "clarification": clarification_message,
                                    "status": "needs_clarification"
                                }
                            else:
                                generated_query = content_text
                                logger.info(f"Found query in output[{i}].content[0].text: {generated_query}")
                                break
                        elif output.content:
                            generated_query = str(output.content[0]).strip()
                            logger.info(f"Found query in output[{i}].content[0]: {generated_query}")
                            break
                        else:
                            generated_query = ""
                    else:
                        generated_query = output.content.strip()
                        logger.info(f"Found query in output[{i}].content: {generated_query}")
                        break
                elif hasattr(output, 'text') and output.text:
                    if isinstance(output.text, list):
                        generated_query = output.text[0].strip() if output.text else ""
                    else:
                        generated_query = output.text.strip()
                    logger.info(f"Found query in output[{i}].text: {generated_query}")
                    break
            
            if not generated_query:
                # Check if we got a message instead of a tool call
                for i, output in enumerate(response.output):
                    if hasattr(output, 'content') and output.content:
                        for content_item in output.content:
                            if hasattr(content_item, 'text') and content_item.text:
                                clarification_message = content_item.text
                                logger.info(f"Got clarification message: {clarification_message}")
                                # Don't try to execute clarification as SQL
                                return {
                                    "query": None,
                                    "clarification": clarification_message,
                                    "status": "needs_clarification"
                                }
                
                # If we get here, we couldn't extract anything useful
                return {
                    "query": None,
                    "clarification": "I couldn't understand your query. Please try rephrasing it.",
                    "status": "needs_clarification"
                }
            
            # Fix common spacing issues
            if generated_query:
                generated_query = generated_query.replace('FROM ordersWHERE', 'FROM orders WHERE')
                generated_query = generated_query.replace('FROM ordersGROUP BY', 'FROM orders GROUP BY')
                generated_query = generated_query.replace('FROM ordersORDER BY', 'FROM orders ORDER BY')
                generated_query = generated_query.replace('FROM ordersLIMIT', 'FROM orders LIMIT')
                
                logger.info(f"Final generated query: {generated_query}")
            
            return {
                "query": generated_query,
                "clarification": clarification_message,
                "status": "success" if generated_query else "needs_clarification"
            }
            
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            raise
