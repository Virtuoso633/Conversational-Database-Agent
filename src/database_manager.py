# src/database_manager.py
from dotenv import load_dotenv
import pymongo
from typing import Dict, List, Any
import logging
from datetime import datetime
load_dotenv()
from bson import ObjectId
import json

class DatabaseManager:
    """
    A class to manage MongoDB database connections and operations.
    This handles connection to MongoDB, schema extraction, and query execution.
    """
    
    def __init__(self, uri: str, database_name: str):
        """
        Initialize the DatabaseManager with MongoDB connection details.
        """
        self.uri = uri
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collections_info = {}
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """
        Establish connection to MongoDB.
        """
        try:
            self.client = pymongo.MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            print(f"✓ Connected to MongoDB database: {self.database_name}")
            self._initialize_collections_info()
            return True
        except Exception as e:
            print(f"✗ Error connecting to MongoDB: {str(e)}")
            # FIX: Ensure self.db is None if connection fails
            self.db = None
            return False
    
    def _initialize_collections_info(self):
        """Initialize collections information cache."""
        # FIX: Explicitly check if self.db is not None
        if self.db is not None:
            try:
                collections = self.get_collections()
                for collection_name in collections:
                    self.collections_info[collection_name] = {
                        'schema': None, 'sample_docs': None, 'last_updated': None
                    }
                print(f"✓ Initialized info for {len(collections)} collections")
            except Exception as e:
                print(f"⚠ Warning: Could not initialize collections info: {str(e)}")
    
    def get_collections(self) -> List[str]:
        """
        Get list of all collections in the database.
        """
        # FIX: Check if the database connection object is None
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        
        try:
            return self.db.list_collection_names()
        except Exception as e:
            self.logger.error(f"Error getting collections: {str(e)}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get basic statistics for a collection.
        """
        # FIX: Check if the database connection object is None
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        
        try:
            collection = self.db[collection_name]
            return {
                'name': collection_name,
                'document_count': collection.count_documents({}),
                'indexes': list(collection.list_indexes())
            }
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return {'error': str(e)}

    def extract_schema(self, collection_name: str, sample_size: int = 100) -> Dict[str, Any]:
        """
        Extract schema information from a collection by sampling documents.
        """
        # FIX: Check if the database connection object is None
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        
        try:
            collection = self.db[collection_name]
            total_docs = collection.count_documents({})
            
            if total_docs == 0:
                return {"error": f"No documents found in collection {collection_name}"}
            
            actual_sample_size = min(sample_size, total_docs)
            pipeline = [{"$sample": {"size": actual_sample_size}}]
            sample_docs = list(collection.aggregate(pipeline))
            
            schema = {
                "collection_name": collection_name,
                "total_documents": total_docs,
                "sample_size": actual_sample_size,
                "fields": {},
                "extracted_at": datetime.now().isoformat()
            }
            
            for doc in sample_docs:
                self._analyze_document_structure(doc, schema["fields"])
            
            for field_info in schema["fields"].values():
                field_info["frequency"] = field_info.get("count", 0) / actual_sample_size
                if isinstance(field_info.get("type"), set):
                    field_info["type"] = list(field_info["type"])
            
            self.collections_info[collection_name]["schema"] = schema
            self.collections_info[collection_name]["last_updated"] = datetime.now()
            
            return schema
        except Exception as e:
            error_msg = f"Error extracting schema from {collection_name}: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
    def _sanitize_document(self, doc):
        """Convert MongoDB-specific types to JSON-serializable formats"""
        if isinstance(doc, list):
            return [self._sanitize_document(item) for item in doc]
        if isinstance(doc, dict):
            return {k: self._sanitize_document(v) for k, v in doc.items()}
        if isinstance(doc, ObjectId):
            return str(doc)  # Convert ObjectId to string
        return doc

    def execute_query(self, collection_name: str, query_type: str, query: Dict[str, Any]) -> Dict[str, Any]:
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        
        collection = self.db[collection_name]
        
        try:
            start_time = datetime.now()
            result = []
            
            if query_type == "find":
                result = self._execute_find_query(collection, query)
            elif query_type == "aggregate":
                result = self._execute_aggregate_query(collection, query)
            elif query_type == "count":
                result = self._execute_count_query(collection, query)
            elif query_type == "distinct":
                result = self._execute_distinct_query(collection, query)
            else:
                raise ValueError(f"Unsupported query type: {query_type}")
            
            # Sanitize results before returning
            sanitized_result = self._sanitize_document(result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "data": sanitized_result,
                "execution_time_seconds": execution_time,
                "result_count": len(sanitized_result)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_document_structure(self, doc: Dict, fields_info: Dict, prefix: str = "") -> None:
        for key, value in doc.items():
            if key == "_id":
                continue
            
            field_name = f"{prefix}.{key}" if prefix else key
            
            if field_name not in fields_info:
                fields_info[field_name] = {"type": set(), "count": 0}
            
            fields_info[field_name]["count"] += 1
            
            if isinstance(value, list):
                fields_info[field_name]["type"].add("array")
                if value and isinstance(value[0], dict):
                    self._analyze_document_structure(value[0], fields_info, f"{field_name}[]")
            elif isinstance(value, dict):
                fields_info[field_name]["type"].add("object")
                self._analyze_document_structure(value, fields_info, field_name)
            else:
                fields_info[field_name]["type"].add(type(value).__name__)
    
    def execute_query(self, collection_name: str, query_type: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a MongoDB query on a collection.
        """
        # FIX: Check if the database connection object is None
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        
        collection = self.db[collection_name]
        
        try:
            start_time = datetime.now()
            result = []
            
            if query_type == "find":
                result = self._execute_find_query(collection, query)
            elif query_type == "aggregate":
                result = self._execute_aggregate_query(collection, query)
            elif query_type == "count":
                result = self._execute_count_query(collection, query)
            elif query_type == "distinct":
                result = self._execute_distinct_query(collection, query)
            else:
                raise ValueError(f"Unsupported query type: {query_type}")
            
            # Always sanitize results before returning
            sanitized_result = self._sanitize_document(result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "data": sanitized_result,
                "execution_time_seconds": execution_time,
                "result_count": len(sanitized_result)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def _execute_find_query(self, collection, query: Dict) -> List[Dict]:
        filter_query = query.get("filter", {})
        projection = query.get("projection", None)
        limit = query.get("limit", 100)
        sort = query.get("sort", None)
        cursor = collection.find(filter_query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if limit > 0:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def _execute_aggregate_query(self, collection, query: Dict) -> List[Dict]:
        pipeline = query.get("pipeline", [])
        if not pipeline:
            raise ValueError("Aggregation pipeline cannot be empty")
        return list(collection.aggregate(pipeline))
    
    def _execute_count_query(self, collection, query: Dict) -> List[Dict]:
        filter_query = query.get("filter", {})
        count = collection.count_documents(filter_query)
        return [{"count": count}]
    
    def _execute_distinct_query(self, collection, query: Dict) -> List[Dict]:
        field = query.get("field", "")
        if not field:
            raise ValueError("Field name is required for distinct query")
        distinct_values = collection.distinct(field, query.get("filter", {}))
        return [{"field": field, "distinct_values": distinct_values, "count": len(distinct_values)}]
    
    def get_sample_documents(self, collection_name: str, limit: int = 5) -> List[Dict]:
    # FIX: Check if the database connection object is None
        if self.db is None:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        
        try:
            docs = list(self.db[collection_name].find().limit(limit))
            return self._sanitize_document(docs)
        except Exception as e:
            self.logger.error(f"Error getting sample documents: {str(e)}")
            return []
    
    def close(self) -> None:
        if self.client:
            self.client.close()
            print("✓ MongoDB connection closed")
            self.logger.info("MongoDB connection closed")


    def get_sample_document(self, collection_name: str) -> dict:
        if self.db is None:
            return {}
        try:
            doc = self.db[collection_name].find_one({}, {'_id': 0})
            return doc if doc else {}
        except Exception:
            return {}

