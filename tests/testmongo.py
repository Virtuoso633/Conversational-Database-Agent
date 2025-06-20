import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "sample_analytics")

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
print(db.dashboard_metrics.find_one())