from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from datetime import datetime
from pymongo import MongoClient
from config.settings import config
import uuid
import logging
load_dotenv()

class ConversationManager:
    """
    Manages conversational context by storing message history
    and logging events to the analytics database.
    """
    def __init__(self, memory_key: str = "history"):
        self.memory = ConversationBufferMemory(
            memory_key=memory_key,
            return_messages=True
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("ConversationManager initialized")
        self.session_id = str(uuid.uuid4())

        # Determine which database to use for analytics:
        # Priority: ANALYTICS_DB (if set) → DATABASE_NAME
        db_name = config.ANALYTICS_DB  # Use the new ANALYTICS_DB value
        self.logger.info(f"Using analytics database: {db_name}")
        self.analytics_db = MongoClient(config.MONGODB_URI)[db_name]

    def add_user_message_to_analytics(self, text: str) -> None:
        """Adds only the user message to the analytics database."""
        self.logger.debug(f"Logging user message to analytics: {text}")
        event = {
            "timestamp": datetime.utcnow(),
            "type": "user_message",
            "text": text,
            "session_id": self.session_id
        }
        self.analytics_db.events.insert_one(event)

    def add_ai_message_to_analytics(self, text: str, intent: dict, success_flag: bool, exec_time: float) -> None:
        """Adds only the AI message and its metadata to the analytics database."""
        self.logger.debug(f"Logging AI message to analytics: {text}")
        event = {
            "timestamp": datetime.utcnow(),
            "type": "ai_response",
            "text": text,
            "session_id": self.session_id,
            "intent": intent,
            "response_success": success_flag,
            "execution_time": exec_time
        }
        self.analytics_db.events.insert_one(event)

    def save_interaction_to_memory(self, user_input: str, ai_output: str) -> None:
        """Saves a complete user-AI interaction to the LangChain memory buffer."""
        self.memory.save_context({"input": user_input}, {"output": ai_output})
        self.logger.debug("Saved interaction to memory.")

    def get_conversation_history(self) -> str:
        """
        Retrieve the full conversation history as a single string.
        """
        return self.memory.load_memory_variables({}).get("history", "")
    
    def handle_ambiguous_query(self, user_input: str) -> str:
        """Store ambiguous query for context in follow-up"""
        context = {
            "type": "ambiguous_query",
            "original_query": user_input,
            "timestamp": datetime.utcnow()
        }
        self.memory.save_context(
            {"input": user_input},
            {"output": "Please clarify your previous query", "context": context}
        )
        return "Your previous query was ambiguous. Please clarify."
