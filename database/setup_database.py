import logging
from .clickhouse_client import ClickHouseClient
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def setup_database():
    """Setup ClickHouse database with sample e-commerce data"""
    client = ClickHouseClient()
    
    try:
        # Create tables
        create_tables(client)
        
        # Check if data exists
        if not check_data_exists(client):
            logger.info("📊 Populating with sample data...")
            populate_sample_data(client)
        else:
            logger.info("✅ Database already contains data")
            
        logger.info("✅ Database setup complete")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

def create_tables(client):
    """Create the necessary tables"""
    tables = [
        {
            "name": "orders",
            "schema": """
                CREATE TABLE IF NOT EXISTS orders (
                    id UInt32,
                    customer_id UInt32,
                    product_id UInt32,
                    order_date DateTime,
                    total_amount Decimal(10, 2),
                    status String,
                    created_at DateTime DEFAULT NOW(),
                    updated_at DateTime DEFAULT NOW()
                ) ENGINE = MergeTree()
                ORDER BY (order_date, id)
            """
        },
        {
            "name": "customers",
            "schema": """
                CREATE TABLE IF NOT EXISTS customers (
                    id UInt32,
                    name String,
                    email String,
                    created_at DateTime DEFAULT NOW()
                ) ENGINE = MergeTree()
                ORDER BY (id)
            """
        },
        {
            "name": "products",
            "schema": """
                CREATE TABLE IF NOT EXISTS products (
                    id UInt32,
                    name String,
                    price Decimal(10, 2),
                    category String,
                    created_at DateTime DEFAULT NOW()
                ) ENGINE = MergeTree()
                ORDER BY (id)
            """
        }
    ]
    
    for table in tables:
        client.client.command(table["schema"])
        logger.info(f"✅ Created table: {table['name']}")

def check_data_exists(client):
    """Check if sample data already exists"""
    try:
        result = client.client.query("SELECT COUNT(*) as count FROM orders")
        return result.result_rows[0][0] > 0
    except Exception:
        return False

def populate_sample_data(client):
    """Populate tables with sample data"""
    # Generate customers
    customers = generate_customers(100)
    insert_customers(client, customers)
    
    # Generate products
    products = generate_products(50)
    insert_products(client, products)
    
    # Generate orders
    orders = generate_orders(1000, len(customers), len(products))
    insert_orders(client, orders)
    
    logger.info(f"✅ Inserted {len(customers)} customers, {len(products)} products, {len(orders)} orders")

def generate_customers(count):
    """Generate sample customer data"""
    customers = []
    for i in range(1, count + 1):
        customers.append({
            "id": i,
            "name": f"Customer {i}",
            "email": f"customer{i}@example.com"
        })
    return customers

def generate_products(count):
    """Generate sample product data"""
    categories = ["Electronics", "Clothing", "Books", "Home", "Sports"]
    products = []
    
    for i in range(1, count + 1):
        products.append({
            "id": i,
            "name": f"Product {i}",
            "price": round(random.uniform(10, 1000), 2),
            "category": random.choice(categories)
        })
    return products

def generate_orders(count, customer_count, product_count):
    """Generate sample order data"""
    statuses = ["pending", "completed", "cancelled", "shipped"]
    orders = []
    
    for i in range(1, count + 1):
        order_date = datetime.now() - timedelta(days=random.randint(0, 365))
        
        orders.append({
            "id": i,
            "customer_id": random.randint(1, customer_count),
            "product_id": random.randint(1, product_count),
            "order_date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "total_amount": round(random.uniform(10, 500), 2),
            "status": random.choice(statuses)
        })
    return orders

def insert_customers(client, customers):
    """Insert customer data"""
    for customer in customers:
        client.client.command(f"""
            INSERT INTO customers (id, name, email) 
            VALUES ({customer['id']}, '{customer['name']}', '{customer['email']}')
        """)

def insert_products(client, products):
    """Insert product data"""
    for product in products:
        client.client.command(f"""
            INSERT INTO products (id, name, price, category) 
            VALUES ({product['id']}, '{product['name']}', {product['price']}, '{product['category']}')
        """)

def insert_orders(client, orders):
    """Insert order data"""
    for order in orders:
        client.client.command(f"""
            INSERT INTO orders (id, customer_id, product_id, order_date, total_amount, status) 
            VALUES ({order['id']}, {order['customer_id']}, {order['product_id']}, '{order['order_date']}', {order['total_amount']}, '{order['status']}')
        """)

if __name__ == "__main__":
    setup_database()
