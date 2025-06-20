# tests/test_database_manager.py
import sys
import os
from dotenv import load_dotenv


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database_manager import DatabaseManager

load_dotenv()

def test_database_manager():
    """Comprehensive test of DatabaseManager functionality."""
    print("=== Testing Database Manager ===\n")
    
    # Initialize DatabaseManager
    db_manager = DatabaseManager(
        uri=os.getenv('MONGODB_URI'),
        database_name=os.getenv('DATABASE_NAME', 'sample_analytics')
    )
    
    try:
        # Test 1: Connection
        print("1. Testing MongoDB Connection...")
        if not db_manager.connect():
            print("❌ Failed to connect to MongoDB")
            return False
        
        # Test 2: Get Collections
        print("\n2. Testing Collection Retrieval...")
        collections = db_manager.get_collections()
        print(f"✓ Found collections: {collections}")
        
        if not collections:
            print("❌ No collections found")
            return False
        
        # Test 3: Collection Statistics
        print("\n3. Testing Collection Statistics...")
        for collection_name in collections[:3]:  # Test first 3 collections
            stats = db_manager.get_collection_stats(collection_name)
            print(f"✓ {collection_name}: {stats.get('document_count', 0)} documents")
        
        # Test 4: Schema Extraction
        print("\n4. Testing Schema Extraction...")
        test_collection = collections[0]  # Use first collection
        schema = db_manager.extract_schema(test_collection, sample_size=10)
        
        if 'error' in schema:
            print(f"❌ Schema extraction failed: {schema['error']}")
        else:
            print(f"✓ Schema extracted for {test_collection}")
            print(f"  - Total documents: {schema.get('total_documents', 0)}")
            print(f"  - Fields found: {len(schema.get('fields', {}))}")
            
            # Show first few field
            fields = schema.get('fields', {})
            for i, (field_name, field_info) in enumerate(list(fields.items())[:3]):
                print(f"  - {field_name}: {field_info.get('type', [])} (frequency: {field_info.get('frequency', 0):.2f})")
        
        # Test 5: Sample Documents
        print(f"\n5. Testing Sample Document Retrieval...")
        sample_docs = db_manager.get_sample_documents(test_collection, limit=2)
        print(f"✓ Retrieved {len(sample_docs)} sample documents")
        
        # Test 6: Basic Queries
        print(f"\n6. Testing Query Execution...")
        
        # Test count query
        count_result = db_manager.execute_query(
            test_collection,
            "count",
            {"filter": {}}
        )
        
        if count_result.get('success'):
            print(f"✓ Count query: {count_result['data'][0]['count']} documents")
        else:
            print(f"❌ Count query failed: {count_result.get('error')}")
        
        # Test find query
        find_result = db_manager.execute_query(
            test_collection,
            "find",
            {"filter": {}, "limit": 3}
        )
        
        if find_result.get('success'):
            print(f"✓ Find query: Retrieved {find_result['result_count']} documents")
        else:
            print(f"❌ Find query failed: {find_result.get('error')}")
        
        print(f"\n🎉 All Database Manager tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False
        
    finally:
        # Clean up
        db_manager.close()

if __name__ == "__main__":
    test_database_manager()
