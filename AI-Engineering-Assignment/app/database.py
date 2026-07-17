import json
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient

# SQLite Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# NoSQL / MongoDB Setup (with fallback JSON Store)
class JSONCollectionFallback:
    def __init__(self, filepath="nosql_fallback.json"):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump([], f)
                
    def insert_one(self, data):
        if "_id" in data:
            data["_id"] = str(data["_id"])
        else:
            import uuid
            data["_id"] = str(uuid.uuid4())
            
        with open(self.filepath, "r") as f:
            db_data = json.load(f)
        db_data.append(data)
        with open(self.filepath, "w") as f:
            json.dump(db_data, f, indent=4)
        return data

    def find_one(self, filter_query):
        with open(self.filepath, "r") as f:
            db_data = json.load(f)
        for doc in db_data:
            match = True
            for k, v in filter_query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    def find(self, filter_query=None):
        with open(self.filepath, "r") as f:
            db_data = json.load(f)
        if not filter_query:
            return db_data
        results = []
        for doc in db_data:
            match = True
            for k, v in filter_query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc)
        return results

mongo_connected = False
try:
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=1000)
    mongo_client.server_info()
    mongo_db = mongo_client["ai_assignment"]
    generations_collection = mongo_db["test_cases"]
    mongo_connected = True
except Exception as e:
    generations_collection = JSONCollectionFallback()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()