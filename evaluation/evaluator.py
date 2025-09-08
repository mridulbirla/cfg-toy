import time
from typing import List, Dict, Any
from .test_cases import TEST_CASES
from cfg.query_generator import QueryGenerator
from database.clickhouse_client import ClickHouseClient
import logging

logger = logging.getLogger(__name__)

class Evaluator:
    def __init__(self, query_generator=None, db_client=None):
        self.query_generator = query_generator or QueryGenerator()
        self.db_client = db_client or ClickHouseClient(auto_connect=False)
    
    def compare_queries(self, generated: str, expected: str) -> bool:
        """Compare generated query with expected query"""
        # Handle None values
        if generated is None:
            return False
        
        # Normalize queries for comparison
        def normalize(query):
            if query is None:
                return ""
            return query.lower().replace(" ", "").replace("'", "").replace('"', "").strip()
        
        normalized_generated = normalize(generated)
        normalized_expected = normalize(expected)
        
        # Check for exact match
        if normalized_generated == normalized_expected:
            return True
        
        # Check for semantic similarity
        generated_words = set(normalized_generated.split())
        expected_words = set(normalized_expected.split())
        
        intersection = generated_words.intersection(expected_words)
        union = generated_words.union(expected_words)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity > 0.8  # 80% similarity threshold
    
    def run_evaluation(self, progress_callback=None) -> Dict[str, Any]:
        """Run all test cases and return evaluation results"""
        # Check if QueryGenerator is functional
        logger.info(f"🔍 Debug: QueryGenerator client is None: {self.query_generator.client is None}")
        logger.info(f"🔍 Debug: QueryGenerator type: {type(self.query_generator)}")
        logger.info(f"🔍 Debug: QueryGenerator client type: {type(self.query_generator.client)}")
        
        if self.query_generator.client is None:
            logger.error("❌ QueryGenerator is not functional - OpenAI API key not configured")
            return {
                "results": [],
                "metrics": {
                    "accuracy": 0.0,
                    "passed_tests": 0,
                    "total_tests": len(TEST_CASES),
                    "average_execution_time": 0.0,
                    "category_breakdown": {}
                },
                "error": "QueryGenerator is not functional - OpenAI API key not configured"
            }
        
        results = []
        total_execution_time = 0
        total_tests = len(TEST_CASES)
        
        logger.info(f"🧪 Starting evaluation with {total_tests} test cases...")
        
        for i, test_case in enumerate(TEST_CASES):
            try:
                logger.info(f"Testing: {test_case['description']}")
                
                start_time = time.time()
                response = self.query_generator.generate_query(
                    test_case['natural_language_query']
                )
                generation_time = (time.time() - start_time) * 1000
                total_execution_time += generation_time
                
                # Extract the query from the response
                if isinstance(response, dict):
                    generated_query = response.get('query')
                    if generated_query is None:
                        generated_query = ""
                else:
                    generated_query = str(response) if response is not None else ""
                
                is_correct = self.compare_queries(generated_query, test_case['expected_query'])
                
                result = {
                    "id": test_case['id'],
                    "test_case": test_case,
                    "generated_query": generated_query,
                    "expected_query": test_case['expected_query'],
                    "is_correct": is_correct,
                    "execution_time": generation_time,
                    "timestamp": time.time()
                }
                
                results.append(result)
                
                status = "✅ PASS" if is_correct else "❌ FAIL"
                logger.info(f"{status} - {test_case['description']}")
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i + 1, total_tests, test_case['description'], status, result)
                
            except Exception as e:
                logger.error(f"❌ Test failed: {test_case['description']} - {e}")
                error_result = {
                    "id": test_case['id'],
                    "test_case": test_case,
                    "generated_query": "",
                    "expected_query": test_case['expected_query'],
                    "is_correct": False,
                    "execution_time": 0,
                    "timestamp": time.time(),
                    "error": str(e)
                }
                results.append(error_result)
                
                # Call progress callback for error case
                if progress_callback:
                    progress_callback(i + 1, total_tests, test_case['description'], "❌ ERROR", error_result)
        
        # Calculate metrics
        metrics = self.calculate_metrics(results, total_execution_time)
        
        logger.info(f"📊 Evaluation complete: {metrics['passed_tests']}/{metrics['total_tests']} tests passed")
        
        return {
            "results": results,
            "metrics": metrics
        }
    
    def calculate_metrics(self, results: List[Dict], total_execution_time: float) -> Dict[str, Any]:
        """Calculate evaluation metrics"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['is_correct'])
        failed_tests = total_tests - passed_tests
        accuracy = passed_tests / total_tests if total_tests > 0 else 0
        average_execution_time = total_execution_time / total_tests if total_tests > 0 else 0
        
        # Category breakdown
        category_breakdown = {}
        categories = ['basic', 'aggregation', 'filtering', 'complex']
        
        for category in categories:
            category_results = [r for r in results if r['test_case']['category'] == category]
            category_total = len(category_results)
            category_passed = sum(1 for r in category_results if r['is_correct'])
            category_accuracy = category_passed / category_total if category_total > 0 else 0
            
            category_breakdown[category] = {
                "total": category_total,
                "passed": category_passed,
                "accuracy": category_accuracy
            }
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "accuracy": accuracy,
            "average_execution_time": average_execution_time,
            "category_breakdown": category_breakdown
        }
