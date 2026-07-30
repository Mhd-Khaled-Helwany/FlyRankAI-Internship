# To run server, use command fastapi dev
# To see message in browser, visit http://localhost:8000/
# To see message in terminal, run command curl -i http://localhost:8000/
# To access a specific endpoint, add the endpoint to the end of the URL, e.g. http://localhost:8000/tasks

from fastapi import FastAPI, HTTPException, status
from fastapi import Depends, Header
from supabase import create_client, Client
from pydantic import BaseModel
import os
from dotenv import load_dotenv


load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class UserInfo(BaseModel):
    email: str
    password: str

app = FastAPI()

# Stage 1: signup endpoint
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(signup_data: UserInfo):
    """Sign up a new user."""
    if not signup_data.email or not signup_data.password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required")
    try:
        response = supabase.auth.sign_up({
            "email": signup_data.email,
            "password": signup_data.password
        })
        return {"message": "User signed up successfully", "user": response.user}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Log in endpoint
@app.post("/auth/login")
async def login(signin_data: UserInfo):
    """Log in an existing user."""
    if not signin_data.email or not signin_data.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": signin_data.email,
            "password": signin_data.password
        })
    except Exception as e:
        auth_status = getattr(e, "status", None)
        if auth_status is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "Invalid login credentials"})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    return {"message": "User Logged in successfully", "access_token": response.session.access_token, "refresh_token": response.session.refresh_token}

# Stage 2: Public endpoint
@app.get("/public/info")
async def public():
    """Public endpoint that does not require authentication."""
    return {"message": "Welcome stranger! This info is public."}

# Stage 3: Dependency for token validation
def check_token(authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={ "error": "Access token required" })
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Malformed Authorization header"}
        )

    token = parts[1]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Malformed Authorization header"}
        )
    try:
        response = supabase.auth.get_user(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": "Invalid or expired token"})
    
    return response.user


# Protected endpoint
@app.get("/protected/profile")
async def protected(response = Depends(check_token)):
    """Protected endpoint that requires a valid access token."""
    
    return {"message": "Access granted", "id": response.id, "email": response.email, "account creation date": response.created_at}

# Stage 4: Logout endpoint
@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response = Depends(check_token)):
    """Log out the user by revoking the access token."""
    try:
        supabase.auth.sign_out()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return