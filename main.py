from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import date, timedelta, datetime, timezone
import os # For generating a secret key if not set

# Security imports
from passlib.context import CryptContext
from jose import JWTError, jwt

# --- Database Imports & Setup ---
import models # Import your SQLAlchemy models - direct import
import database # Import database utilities - direct import
from sqlalchemy.orm import Session # For type hinting DB session

# Create database tables if they don't exist
# This should ideally be handled by a migration tool like Alembic in production,
# but for simplicity, we'll create them on startup here.
database.Base.metadata.create_all(bind=database.engine)

# --- Data Seeding ---
def seed_initial_jobs(db: Session):
    # Check if jobs already exist
    if db.query(models.JobPost).first() is None:
        sample_jobs_data = [
            {
                "posted_date": date(2023, 10, 26),
                "status": "Hiring",
                "title": "Software Engineer",
                "company": "FruitPie Tech",
                "description": "Developing the core fruit sorting algorithms.",
                "requirements": "Python, FastAPI, 3+ years experience",
                "location": "Apple Valley, CA",
                "salary": "$100,000 - $120,000",
                "contact": "hr@fruitpietech.com",
                "notes": "Great team, lots of free fruit!"
            },
            {
                "posted_date": date(2023, 11, 5),
                "status": "Hiring",
                "title": "UX Designer",
                "company": "OrangeBloom Inc.",
                "description": "Designing intuitive interfaces for our citrus marketplace.",
                "requirements": "Figma, Adobe XD, User Research",
                "location": "Orange County, FL",
                "salary": "$90,000 - $110,000",
                "contact": "careers@orangebloom.com",
                "notes": "Sunny office environment."
            },
            {
                "posted_date": date(2023, 11, 15),
                "status": "Closed",
                "title": "Data Analyst",
                "company": "BerryMetrics Co.",
                "description": "Analyzing sales data for berry-based products.",
                "requirements": "SQL, Python, Tableau",
                "location": "Remote (US)",
                "contact": "jobs@berrymetrics.com",
                "notes": "Position filled quickly."
            }
        ]
        for job_data in sample_jobs_data:
            db_job = models.JobPost(**job_data)
            db.add(db_job)
        db.commit()
        print("Sample jobs seeded into the database.")

# Seed data on startup if needed
# Create a temporary session for seeding
db_session_for_seeding = database.SessionLocal()
try:
    seed_initial_jobs(db_session_for_seeding)
finally:
    db_session_for_seeding.close()

# Configuration for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-for-dev-only") # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for required authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# OAuth2 scheme for optional authentication
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# --- Pydantic Models (Schemas) ---

class UserBase(BaseModel):
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str
    is_poster: bool = False
    is_seeker: bool = True # Default to seeker
    # No model_config needed here as it's for input only, not from ORM

class User(UserBase): # For returning user info, no password
    id: int
    is_poster: bool
    is_seeker: bool
    disabled: Optional[bool] = None
    # model_config = ConfigDict(from_attributes=True) # Already inherited from UserBase

# UserInDB is no longer needed as a Pydantic model, SQLAlchemy model models.User is used directly for DB representation
# class UserInDB(User):
#     hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class JobPost(BaseModel): # This is our Pydantic schema for Job Posts
    id: int # Add id field
    posted_date: date
    status: str
    title: str
    company: str
    description: str
    requirements: str
    location: str
    salary: Optional[str] = None
    contact: str
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- In-memory "Database" (Users - To be fully replaced) ---
# fake_users_db = {} # This was removed as we use the DB
# next_user_id = 1 # This was removed

# Sample Job Data (We'll move this to a seeding function)
# sample_jobs = [ ... ] # This global list is now removed/handled by seeding

# --- Utility Functions ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # Use configured expiration
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_db(db: Session, username: str) -> Optional[models.User]: # New DB version
    return db.query(models.User).filter(models.User.username == username).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_from_db(db, username=token_data.username) # New DB call
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user # Returns SQLAlchemy model

# A dependency to make authentication optional
async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(database.get_db)):
    if not token: # If no token was provided (because auto_error=False)
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None # Token exists but no username in it
        token_data = TokenData(username=username)
    except JWTError:
        return None # Token is invalid (e.g., expired, wrong signature)
    
    user = get_user_from_db(db, username=token_data.username) # New DB call
    if user and user.disabled:
        return None
    return user


# --- API Endpoints ---

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user_from_db = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user_from_db or not verify_password(form_data.password, user_from_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_from_db.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/register", response_model=User)
async def register_user(user_data: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # Basic password complexity (example: min 8 chars)
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    hashed_password = get_password_hash(user_data.password)
    
    # Ensure at least one role is selected, or default if needed
    if not user_data.is_poster and not user_data.is_seeker:
        # Defaulting to seeker if no role is explicitly chosen,
        # or you could raise an error if a choice is mandatory.
        user_data.is_seeker = True 

    new_db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_poster=user_data.is_poster,
        is_seeker=user_data.is_seeker,
        disabled=False
    )
    db.add(new_db_user)
    db.commit()
    db.refresh(new_db_user)
    
    # Return User model (without hashed_password)
    return User(
        id=new_db_user.id,
        username=new_db_user.username,
        email=new_db_user.email,
        is_poster=new_db_user.is_poster,
        is_seeker=new_db_user.is_seeker,
        disabled=new_db_user.disabled
    )


@app.get("/")
async def read_root(request: Request, current_user: Optional[User] = Depends(get_current_user_optional), db: Session = Depends(database.get_db)):
    # 'current_user' will be None if not logged in or token is invalid/expired
    # 'current_user' will be the User object if logged in
    # The frontend will handle blurring based on whether it has a token and can successfully get user info
    
    # For now, we always pass the jobs. The frontend will decide what to do.
    # Later, we could restrict data access here based on current_user roles.
    user_info = None
    if current_user:
        user_info = {
            "username": current_user.username,
            "is_poster": current_user.is_poster,
            "is_seeker": current_user.is_seeker
        }
    
    current_year = datetime.now(timezone.utc).year # Get current year

    # Fetch jobs from DB
    db_jobs = db.query(models.JobPost).order_by(models.JobPost.posted_date.desc()).all()
    # Convert SQLAlchemy JobPost objects to Pydantic JobPost models if necessary for the template,
    # or ensure template can handle SQLAlchemy objects directly. For simplicity, let's assume Pydantic models are preferred.
    # If JobPost Pydantic model is the same as the one used for sample_jobs, this should work.
    # We might need to update the Pydantic JobPost model to include an id and enable ORM mode.

    return templates.TemplateResponse("index.html", {
        "request": request,
        "jobs": db_jobs, # Pass database jobs
        "user": user_info, # Pass user_info (or None) to the template
        "current_year": current_year # Add current year to context
    })
    
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    # This endpoint can be used by the frontend to verify a token and get user details
    return current_user


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 