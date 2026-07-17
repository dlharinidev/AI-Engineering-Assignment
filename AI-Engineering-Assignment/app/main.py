from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from .database import engine, Base
from .routes import router

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tri9T AI Engineering Assignment")

app.include_router(router)

@app.get("/")
def health_check():
    return {"status": "online", "system": "CT-200 Parser"}