import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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


@app.post("/auth/signup", summary="Sign Up", status_code=201)
async def signup(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"}
        )

    try:
        result = supabase.auth.sign_up({"email": email, "password": password})
        return {"user": result.user.model_dump() if result.user else None}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )


@app.post("/auth/login", summary="Log In", status_code=200)
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return JSONResponse(
            status_code=400,
            content={"error": "Email and password are required"}
        )

    try:
        result = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "user": result.user.model_dump() if result.user else None
        }
    except Exception:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid login credentials"}
        )


@app.get("/public/info", summary="Public Info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


def extract_token(request: Request):
    """
    Pulls the bearer token out of the Authorization header.
    Returns the token string, or None if it's missing/malformed.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "").strip()
    return token if token else None


@app.get("/protected/profile", summary="Get Profile (protected)")
def get_profile(request: Request):
    token = extract_token(request)

    if not token:
        return JSONResponse(
            status_code=401,
            content={"error": "Access token required"}
        )

    try:
        user_response = supabase.auth.get_user(token)
    except Exception:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"}
        )

    if not user_response or not user_response.user:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"}
        )

    user = user_response.user
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at)
    }