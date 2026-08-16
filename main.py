import os
from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="Auth API",
    description="A FastAPI service using Supabase Auth for signup, login, and protected routes.",
    version="1.0"
)


@app.on_event("startup")
def on_startup():
    print("Server running and connected to Supabase")


@app.get("/", summary="API Information")
def root():
    return {
        "name": "Auth API",
        "version": "1.0"
    }