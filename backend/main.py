from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from jose import jwt
import uuid

# ---------------- CONFIG ----------------
SECRET = "secret123"
ALGO = "HS256"

app = FastAPI()
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # React URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ---------------- DB ----------------
engine = create_engine(
    "sqlite:///sweet.db",
    connect_args={"check_same_thread": False}
)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ---------------- MODELS ----------------
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

class Sweet(Base):
    __tablename__ = "sweets"
    id = Column(String, primary_key=True)
    name = Column(String)
    category = Column(String)
    price = Column(Float)
    quantity = Column(Integer)

Base.metadata.create_all(engine)

# ---------------- SCHEMAS ----------------
class AuthRequest(BaseModel):
    email: str
    password: str

class SweetRequest(BaseModel):
    name: str
    category: str
    price: float
    quantity: int

# ---------------- AUTH ----------------
@app.post("/api/auth/register")
def register(data: AuthRequest):
    db = Session()
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        password=data.password,  # plain password (OK for demo)
        role="USER"
    )
    db.add(user)
    db.commit()
    return {"message": "User registered"}

# ✅ FIXED LOGIN (FORM DATA FOR OAUTH2)
@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = Session()

    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or user.password != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode(
        {"id": user.id, "role": user.role},
        SECRET,
        algorithm=ALGO
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def get_user(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, SECRET, algorithms=[ALGO])

# ---------------- SWEETS ----------------
@app.post("/api/sweets")
def add_sweet(data: SweetRequest, user=Depends(get_user)):
    db = Session()
    sweet = Sweet(
        id=str(uuid.uuid4()),
        name=data.name,
        category=data.category,
        price=data.price,
        quantity=data.quantity
    )
    db.add(sweet)
    db.commit()
    return sweet

@app.get("/api/sweets")
def get_sweets():
    db = Session()
    return db.query(Sweet).all()
