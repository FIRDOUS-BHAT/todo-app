from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Todo Model


class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)

# Dependency to get DB session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models


class TodoBase(BaseModel):
    title: str
    description: str | None = None


class TodoCreate(TodoBase):
    pass


class TodoUpdate(TodoBase):
    completed: bool | None = None


class TodoResponse(TodoBase):
    id: int
    completed: bool

    class Config:
        from_attributes = True


app = FastAPI(title="FastAPI CRUD on Azure")

# CRUD Endpoints


@app.post("/todos/", response_model=TodoResponse)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = Todo(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.get("/todos/{todo_id}", response_model=TodoResponse)
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.get("/todos/", response_model=list[TodoResponse])
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    todos = db.query(Todo).offset(skip).limit(limit).all()
    return todos


@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    update_data = todo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)
    db.commit()
    db.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return {"detail": "Todo deleted"}
