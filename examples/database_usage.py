# examples/database_usage.py
import sys
import os
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database_manager import DatabaseManager

load_dotenv()

def demonstrate_database_operations():
    """Demonstrate various database operations."""
    print("=== Database Manager Usage Examples ===\n")
    
    # Initialize and connect
    db_manager = DatabaseManager(
        uri=os.getenv('MONGODB_URI'),
        database_name=os.getenv('DATABASE_NAME', 'sample_analytics')
    )
    
    if not db_manager.connect():
        print("Failed to connect to database")
        return
    
    try:
        collections = db_manager.get_collections()
        print(f"Available collections: {collections}\n")
        
        # Demonstrate operations on each collection
        for collection in ['customers', 'accounts', 'transactions']:
            if collection in collections:
                print(f"--- {collection.upper()} Collection ---")
                
                # Get schema
                schema = db_manager.extract_schema(collection, sample_size=20)
                print(f"Total documents: {schema.get('total_documents', 0)}")
                
                # Show field information
                fields = schema.get('fields', {})
                print(f"Fields ({len(fields)}):")
                for field_name, field_info in list(fields.items())[:5]:
                    types = ', '.join(field_info.get('type', []))
                    freq = field_info.get('frequency', 0)
                    print(f"  • {field_name}: {types} (appears in {freq:.1%} of documents)")
                
                # Sample query
                result = db_manager.execute_query(
                    collection,
                    "find",
                    {"filter": {}, "limit": 2}
                )
                
                if result.get('success'):
                    print(f"Sample documents: {result['result_count']} retrieved")
                
                print()  # Empty line for separation
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    demonstrate_database_operations()
