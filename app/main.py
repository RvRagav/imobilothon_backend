from fastapi import FastAPI
from dotenv import load_dotenv
from app.db import models
from app.db.database import engine
load_dotenv()

app = FastAPI(title="A.V.I.D Imobilothon Backend")

@app.get("/")
def root():
    return {"message": "Welcome to A.V.I.D Imobilothon Backend"}