import os
from dotenv import load_dotenv
import pymongo
from groq import Groq

def test_environment_setup():
    """Test if all environment variables are loaded correctly"""
    load_dotenv()
    
    mongodb_uri = os.getenv('MONGODB_URI')
    groq_key = os.getenv('GROQ_API_KEY')
    
    print("Environment Variables Check:")
    print(f"MongoDB URI loaded: {'✓' if mongodb_uri else '✗'}")
    print(f"Groq API Key loaded: {'✓' if groq_key else '✗'}")
    
    return mongodb_uri, groq_key

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        load_dotenv()
        client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
        
        # Test connection
        client.admin.command('ping')
        print("MongoDB Connection: ✓ Connected successfully")
        
        # List databases
        db_names = client.list_database_names()
        print(f"Available databases: {db_names}")
        
        # Check if sample_analytics exists
        if 'sample_analytics' in db_names:
            print("Sample Analytics Database: ✓ Found")
            
            # Check collections
            db = client['sample_analytics']
            collections = db.list_collection_names()
            print(f"Collections in sample_analytics: {collections}")
            
            return True
        else:
            print("Sample Analytics Database: ✗ Not found")
            return False
            
    except Exception as e:
        print(f"MongoDB Connection: ✗ Failed - {str(e)}")
        return False

def test_groq_connection():
    """Test Groq API connection"""
    try:
        load_dotenv()
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        # Test with a simple completion using Llama model
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10,
            temperature=0
        )
        
        print("Groq API Connection: ✓ Connected successfully")
        print(f"Test response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"Groq API Connection: ✗ Failed - {str(e)}")
        return False

def test_langchain_groq_integration():
    """Test LangChain-Groq integration"""
    try:
        from langchain_groq import ChatGroq
        
        load_dotenv()
        
        # Initialize ChatGroq
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            api_key=os.getenv('GROQ_API_KEY')
        )
        
        # Test a simple query
        response = llm.invoke("Say 'LangChain-Groq integration working!'")
        print("LangChain-Groq Integration: ✓ Working successfully")
        print(f"LangChain response: {response.content}")
        return True
        
    except Exception as e:
        print(f"LangChain-Groq Integration: ✗ Failed - {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Testing Groq-Based Project Setup ===\n")
    
    # Test environment setup
    mongodb_uri, groq_key = test_environment_setup()
    print()
    
    # Test MongoDB connection
    mongodb_success = test_mongodb_connection()
    print()
    
    # Test Groq connection
    groq_success = test_groq_connection()
    print()
    
    # Test LangChain-Groq integration
    langchain_success = test_langchain_groq_integration()
    print()
    
    # Final summary
    print("=== Setup Summary ===")
    print(f"Environment Variables: {'✓' if mongodb_uri and groq_key else '✗'}")
    print(f"MongoDB Connection: {'✓' if mongodb_success else '✗'}")
    print(f"Groq API: {'✓' if groq_success else '✗'}")
    print(f"LangChain-Groq Integration: {'✓' if langchain_success else '✗'}")
    
    if mongodb_success and groq_success and langchain_success:
        print("\n🎉 All tests passed! Your Groq-based environment is ready for development.")
    else:
        print("\n⚠️ Some tests failed. Please check your configuration.")
