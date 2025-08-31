# Test cases for evaluation
TEST_CASES = [
    {
        "id": "basic-count",
        "natural_language_query": "count all orders",
        "expected_query": "SELECT COUNT(*) FROM orders;",
        "description": "Basic count query",
        "category": "basic"
    },
    {
        "id": "sum-amount",
        "natural_language_query": "sum the total amount of all orders",
        "expected_query": "SELECT SUM(total_amount) FROM orders;",
        "description": "Sum aggregation query",
        "category": "aggregation"
    },
    {
        "id": "time-filter",
        "natural_language_query": "sum the total of all orders placed in the last 30 hours",
        "expected_query": "SELECT SUM(total_amount) FROM orders WHERE order_date >= NOW() - INTERVAL 30 HOUR;",
        "description": "Time-based filtering with aggregation",
        "category": "filtering"
    },
    {
        "id": "status-filter",
        "natural_language_query": "count orders with status completed",
        "expected_query": "SELECT COUNT(*) FROM orders WHERE status = 'completed';",
        "description": "Status filtering",
        "category": "filtering"
    },
    {
        "id": "complex-aggregation",
        "natural_language_query": "average order amount by status",
        "expected_query": "SELECT status, AVG(total_amount) FROM orders GROUP BY status;",
        "description": "Group by aggregation",
        "category": "complex"
    }
]
