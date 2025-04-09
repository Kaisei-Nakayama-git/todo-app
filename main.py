from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta

# -------------------- FastAPI Setup --------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- DB Setup --------------------
DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# -------------------- Models --------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    todos = relationship("TodoDB", back_populates="owner")

class TodoDB(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="todos")

Base.metadata.create_all(bind=engine)

# -------------------- Auth --------------------
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="認証エラー")
    except JWTError:
        raise HTTPException(status_code=401, detail="トークン不正")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません")
    return user

# -------------------- Pydantic Schemas --------------------
class Todo(BaseModel):
    title: str
    done: bool = False

# -------------------- Routes --------------------
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/register")
def register(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if user:
        raise HTTPException(status_code=400, detail="ユーザー名は既に存在します")
    hashed_password = get_password_hash(form_data.password)
    new_user = User(username=form_data.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "登録完了！"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="ログイン情報が間違っています")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/todos")
def get_todos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    todos = db.query(TodoDB).filter(TodoDB.owner_id == current_user.id).all()
    return [{"title": t.title, "done": t.done} for t in todos]

@app.post("/todos")
def add_todo(todo: Todo, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_todo = TodoDB(title=todo.title, done=todo.done, owner_id=current_user.id)
    db.add(new_todo)
    db.commit()
    return {"message": "タスクを追加しました！"}

@app.put("/todos/{index}")
def mark_done(index: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    todos = db.query(TodoDB).filter(TodoDB.owner_id == current_user.id).all()
    if 0 <= index < len(todos):
        todos[index].done = True
        db.commit()
        return {"message": "完了にしました！"}
    return {"error": "Index不正"}

@app.delete("/todos/{index}")
def delete_todo(index: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    todos = db.query(TodoDB).filter(TodoDB.owner_id == current_user.id).all()
    if 0 <= index < len(todos):
        db.delete(todos[index])
        db.commit()
        return {"message": "削除しました！"}
    return {"error": "Index不正"}