import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# HTTPBearer is what tells Swagger UI "this API uses bearer tokens" --
# it's what makes the lock icon and "Authorize" button appear at /docs.
# auto_error=False lets us return our own custom 401 JSON message instead
# of FastAPI's default error shape when the header is missing.
bearer_scheme = HTTPBearer(auto_error=False)


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


# ---------------------------------------------------------------------------
# Auth dependency -- now using FastAPI's HTTPBearer scheme so Swagger UI
# knows these routes are protected and shows the Authorize padlock.
# ---------------------------------------------------------------------------

def get_verified_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Access token required")

    token = credentials.credentials.strip()

    if not token:
        raise HTTPException(status_code=401, detail="Access token required")

    try:
        user_response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user_response or not user_response.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    request.state.token = token
    request.state.user = user_response.user

    return token


@app.get("/protected/profile", summary="Get Profile (protected)")
def get_profile(request: Request, token: str = Depends(get_verified_token)):
    user = request.state.user
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at)
    }


@app.get("/protected/dashboard", summary="Get Dashboard (protected)")
def get_dashboard(request: Request, token: str = Depends(get_verified_token)):
    user = request.state.user
    return {
        "message": f"Welcome to your dashboard, {user.email}!",
        "id": user.id
    }


@app.post("/auth/logout", summary="Log Out", status_code=204)
def logout(request: Request, token: str = Depends(get_verified_token)):
    try:
        supabase.auth.sign_out(token)
    except Exception:
        pass
    return None