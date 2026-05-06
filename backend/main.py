import os
import secrets
import asyncio
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import engine, get_db, Base, SessionLocal
from models import User, VirtualMachine
from celery_worker import send_activation_email

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey123")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

Base.metadata.create_all(bind=engine)


def seed_vms():
    db = SessionLocal()
    if db.query(VirtualMachine).count() == 0:
        vms = [
            VirtualMachine(name="proxy-1", host="192.168.1.100", port=1080, protocol="socks5"),
            VirtualMachine(name="proxy-2", host="192.168.1.101", port=1080, protocol="socks5"),
            VirtualMachine(name="proxy-3", host="192.168.1.102", port=8080, protocol="http"),
        ]
        for vm in vms:
            db.add(vm)
        db.commit()
        print("seed vms ok")
    db.close()


seed_vms()

app = FastAPI(title="Proxy Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- schemas ---

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str
    password_confirm: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class ChangePassSchema(BaseModel):
    old_password: str
    new_password: str

class ActivateKeySchema(BaseModel):
    key: str


# --- helpers ---

def hash_pw(pw):
    return pwd_context.hash(pw)

def check_pw(pw, hashed):
    return pwd_context.verify(pw, hashed)

def make_token(user_id: int):
    data = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    # пробовал через .get(user_id) но sqlalchemy 2.x не поддерживает
    # user = db.query(User).get(user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# --- auth routes ---

@app.post("/api/auth/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    print(f"[register] {data.email}")

    if data.password != data.password_confirm:
        raise HTTPException(status_code=400, detail="Passwords don't match")

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    key = secrets.token_hex(16)
    user = User(
        email=data.email,
        password=hash_pw(data.password),
        activation_key=key,
    )
    db.add(user)
    db.commit()

    # TODO: добавить срок действия ключа (activation_key_expires)
    send_activation_email.delay(data.email, key)

    return {"message": "Registered! Check your email for the activation key."}


@app.post("/api/auth/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not check_pw(data.password, user.password):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    token = make_token(user.id)
    print(f"[login] user_id={user.id}")
    return {"access_token": token, "token_type": "bearer"}


# --- user routes ---

@app.get("/api/users/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "activation_key": current_user.activation_key,
    }


@app.post("/api/users/refresh-key")
def refresh_key(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_key = secrets.token_hex(16)
    current_user.activation_key = new_key
    db.commit()
    db.refresh(current_user)

    send_activation_email.delay(current_user.email, new_key)
    return {"message": "New key sent to your email"}


@app.post("/api/users/change-password")
def change_password(data: ChangePassSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not check_pw(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Wrong current password")

    current_user.password = hash_pw(data.new_password)
    db.commit()
    return {"message": "Password changed"}


# --- proxy routes ---

@app.post("/api/activate-key")
def activate_key(data: ActivateKeySchema, db: Session = Depends(get_db)):
    print(f"[activate-key] key={data.key}")

    user = db.query(User).filter(User.activation_key == data.key).first()
    if not user:
        raise HTTPException(status_code=400, detail="Key not found or already used")

    # ищем свободную виртуалку
    # сначала пробовал order_by(VirtualMachine.id) но без разницы
    vm = db.query(VirtualMachine).filter(
        VirtualMachine.current_user_id == None,
        VirtualMachine.is_active == True,
    ).first()

    if not vm:
        raise HTTPException(status_code=503, detail="All proxies are busy, try later")

    vm.current_user_id = user.id
    vm.last_used_at = datetime.utcnow()
    user.activation_key = None
    user.is_active = True
    db.commit()

    print(f"[activate-key] user {user.id} -> {vm.host}:{vm.port}")

    return {"host": vm.host, "port": vm.port, "protocol": vm.protocol, "user_id": user.id}


@app.post("/api/disconnect-by-user/{user_id}")
def disconnect_user(user_id: int, db: Session = Depends(get_db)):
    vm = db.query(VirtualMachine).filter(VirtualMachine.current_user_id == user_id).first()
    if vm:
        vm.current_user_id = None
        db.commit()
        print(f"[disconnect] user {user_id} freed vm {vm.id}")
    return {"message": "ok"}


# --- websocket ---

@app.websocket("/ws/status/{user_id}")
async def ws_status(websocket: WebSocket, user_id: int):
    await websocket.accept()
    print(f"[ws] user {user_id} connected")
    try:
        while True:
            db = SessionLocal()
            vm = db.query(VirtualMachine).filter(VirtualMachine.current_user_id == user_id).first()

            if vm:
                await websocket.send_json({
                    "status": "connected",
                    "host": vm.host,
                    "port": vm.port,
                    "protocol": vm.protocol,
                })
            else:
                await websocket.send_json({"status": "disconnected"})

            db.close()
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        print(f"[ws] user {user_id} disconnected")
