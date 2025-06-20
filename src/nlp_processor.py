# # src/nlp_processor.py
# import os
# import json
# from typing import Dict, Any
# from groq import Groq
# from langchain_groq import ChatGroq
# from config.settings import config
# from src.database_manager import DatabaseManager

# class NLPProcessor:
#     """
#     Handles natural language processing by converting user text into
#     MongoDB queries using Groq LLMs and DatabaseManager schema info.
#     """
#     def __init__(self, db_manager: DatabaseManager):
#         """
#         Initialize the NLPProcessor with a connected DatabaseManager instance.
#         """
#         self.db_manager = db_manager
#         self.llm = ChatGroq(
#             model=config.MODEL_NAME,
#             temperature=config.GROQ_TEMPERATURE,
#             api_key=config.GROQ_API_KEY
#         )

#     def parse_query(self, user_text: str, collection_name: str) -> Dict[str, Any]:
#         """
#         Parse user_text into a MongoDB query dict for the specified collection.
#         Returns a dictionary with 'query_type' and parameters.
#         """
#         # Retrieve schema to inform LLM about field names
#         schema = self.db_manager.extract_schema(collection_name)

#         # FIX: Check if schema extraction was successful before using the 'fields' key [1].
#         if 'error' in schema:
#             # If there was an error (e.g., collection not found, empty),
#             # we cannot generate a query. Return an error that can be handled.
#             return {
#                 "query_type": "error",
#                 "error": f"Failed to get schema for collection '{collection_name}'",
#                 "details": schema.get('error')
#             }
        
#         # Now it is safe to access the 'fields' key
#         schema_fields = schema.get('fields', {})

#         # Construct a clear prompt for the LLM
#         prompt = (
#             f"Based on the user's question, generate a JSON object for a MongoDB query. "
#             f"The user's question is: '{user_text}'. "
#             f"The query will run on the '{collection_name}' collection. "
#             f"The available fields and their types are: {json.dumps(schema_fields, indent=2)}. "
#             f"Your response must be a single JSON object with the following keys: "
#             f"'query_type' (can be 'find', 'aggregate', 'count', or 'distinct'), "
#             f"and other relevant keys like 'filter', 'projection', or 'pipeline'. "
#             f"Do not include any explanations, just the JSON object."
#         )

#         try:
#             response = self.llm.invoke(prompt)
#             # The response content from Groq might be a string that needs to be parsed
#             query_dict = json.loads(response.content)
#         except (json.JSONDecodeError, Exception) as e:
#             # Fallback for non-JSON responses or other errors
#             print(f"Error parsing LLM response: {e}")
#             query_dict = {"query_type": "find", "filter": {}, "projection": None}
            
#         return query_dict

#     def execute_intent(self, collection_name: str, intent: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Execute the parsed intent dict on MongoDB and return the result.
#         """
#         # This function does not need changes
#         result = self.db_manager.execute_query(
#             collection_name=collection_name,
#             query_type=intent.get("query_type", "find"),
#             query=intent
#         )
#         return result


# src/nlp_processor.py
import json
import re
from datetime import datetime
from bson import ObjectId
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from config.settings import config
from src.database_manager import DatabaseManager

US_STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY"
}

def extract_state_from_text(user_text: str):
    user_text_lower = user_text.lower()
    for state in US_STATES:
        if state in user_text_lower:
            return state
    return None

class NLPProcessor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.llm = ChatGroq(
            model=config.MODEL_NAME,
            temperature=config.GROQ_TEMPERATURE,
            api_key=config.GROQ_API_KEY
        )

    def _json_serial(self, obj):
        if isinstance(obj, (datetime, ObjectId)):
            return str(obj)
        if isinstance(obj, dict):
            return {k: self._json_serial(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._json_serial(item) for item in obj]
        return obj

    def parse_query(
        self,
        user_text: str,
        collection_name: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        schema = self.db_manager.extract_schema(collection_name)
        if 'error' in schema:
            return {
                "query_type": "error",
                "error_type": "schema",
                "error_message": f"Schema error: {schema.get('error')}"
            }
        simplified_fields = {}
        for field_name, field_info in schema.get('fields', {}).items():
            simplified_fields[field_name] = {
                "types": list(field_info.get("type", []))[:3],
                "sample_values": field_info.get("sample_values", [])[:1]
            }
            if len(simplified_fields) >= 15:
                break
        sample_doc = self._get_sample_document(collection_name)
        sample_doc_str = json.dumps(self._json_serial(sample_doc), indent=2)

        # --- State validation logic ---
        if re.search(r"customers\s+(in|from|living in|residing in)\s", user_text.lower()):
            state_name = extract_state_from_text(user_text)
            if state_name is None:
                return {
                    "query_type": "error",
                    "error_type": "impossible",
                    "error_message": "No such US state found in query."
                }

        # --- Session context handling for follow-ups ---
        # session_context should be a dict with at least 'last_filter' and 'last_query_type'
        context_str = ""
        if session_context:
            if session_context.get("last_filter"):
                context_str += f"Previous filter: {json.dumps(session_context['last_filter'])}\n"
            if session_context.get("last_query_type"):
                context_str += f"Previous query type: {session_context['last_query_type']}\n"
            if session_context.get("last_projection"):
                context_str += f"Previous projection: {json.dumps(session_context['last_projection'])}\n"

        # --- Prompt for multi-turn and cross-collection context ---
        prompt = (
            "You are an expert MongoDB query generator. "
            f"{context_str}"
            f"User question: '{user_text}'\n"
            f"Collection: {collection_name}\n"
            f"Available fields: {', '.join(simplified_fields.keys())}\n"
            f"Data format example: {sample_doc_str}\n"
            "Instructions:\n"
            "- Always output ONLY a single JSON object with keys: query_type, filter, projection, pipeline, or error_type as appropriate. DO NOT return Python code, explanations, or extra text.\n"
            "- If the user asks for customers in a US state, convert the state name to its two-letter postal abbreviation before searching the address field. "
            "For example, if the user asks for 'Customers in California', output:\n"
            "Recognize variations like 'customers from', 'customers living in', etc."
            "{\"query_type\": \"find\", \"filter\": {\"address\": {\"$regex\": \"\\\\bCA\\\\b\", \"$options\": \"i\"}}, \"projection\": {}, \"pipeline\": []}\n"
            "- If the user asks for a location that is not a real US state, return: {\"query_type\": \"error\", \"error_type\": \"impossible\"}\n"
            "- If the user asks 'How many customers are there?', output:\n"
            "{\"query_type\": \"count\", \"filter\": {}}\n"
            "- If the user asks 'How many customers are there in California?', output:\n"
            "{\"query_type\": \"count\", \"filter\": {\"address\": {\"$regex\": \"\\\\bCA\\\\b\", \"$options\": \"i\"}}}\n"
            "- If the user says 'Show only their names' after a previous filter, output a find query with the same filter and a projection for only the 'name' field.\n"
            "- If the user asks for accounts with a balance > 10000, output:\n"
            "{\"query_type\": \"find\", \"filter\": {\"balance\": {\"$gt\": 10000}}, \"projection\": {}, \"pipeline\": []}\n"
            "- If the user says 'Show ...' or 'List ...', always generate a 'find' query with an appropriate filter and projection. Example: 'Show customers with email from gmail.com' → {\"query_type\": \"find\", \"filter\": {\"email\": {\"$regex\": \"gmail.com\", \"$options\": \"i\"}}, \"projection\": {}, \"pipeline\": []}\n"
            "- If the user says 'How many ...', always generate a 'count' query with the appropriate filter.\n"
            "- If the user asks 'How many are there?' after a previous filter, output a count query with the same filter as the previous turn.\n"
            "- If the user asks for a field that does not exist, return: {\"query_type\": \"error\", \"error_type\": \"impossible\"}\n"
            "- If the user asks an ambiguous question or uses references like 'these', 'them', or 'their', use the session context to resolve them. If still ambiguous, return: {\"query_type\": \"error\", \"error_type\": \"ambiguous\"}\n"
            "- If the user asks for a field subset (e.g., 'Show only their names'), use the 'projection' key to return only those fields.\n"
            "- If the user asks for a group or aggregation, use the 'pipeline' key for MongoDB aggregation pipelines.\n"
            "- If the user asks for a distinct value, use the 'query_type': 'distinct' and specify the field.\n"
            "- Always use the session context to resolve ambiguous references. If you cannot resolve, return an 'ambiguous' error as above.\n"
            "- Never return explanations, only the JSON object as described.\n"
            "- If you cannot generate a valid query, return: {\"query_type\": \"error\", \"error_type\": \"impossible\"}\n"
            "- If the question is ambiguous and cannot be resolved, return: {\"query_type\": \"error\", \"error_type\": \"ambiguous\"}\n"
        )

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            print("LLM raw output:", content)
            if '```json' in content:
                match = re.search(r'```json(.*?)```', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
            elif '```' in content:
                match = re.search(r'```(.*?)```', content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
            if not content or not content.startswith("{"):
                return {
                    "query_type": "error",
                    "error_type": "processing",
                    "error_message": f"LLM returned no valid JSON: {content[:100]}"
                }
            return json.loads(content)
        except Exception as e:
            return {
                "query_type": "error",
                "error_type": "processing",
                "error_message": f"LLM processing failed: {str(e)}"
            }

    def execute_intent(self, collection_name: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        return self.db_manager.execute_query(
            collection_name=collection_name,
            query_type=intent.get("query_type", "find"),
            query=intent
        )
    
    def _get_sample_document(self, collection_name: str) -> dict:
        sample = self.db_manager.get_sample_document(collection_name)
        if sample:
            sample.pop('_id', None)
            sample.pop('tier_and_details', None)
        return sample if sample else {"error": "No sample document available"}