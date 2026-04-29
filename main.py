from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import case
from datetime import date
import models
from database import engine, Base, get_db, get_current_user
from auth import create_token
import os

app = FastAPI()

Base.metadata.create_all(bind=engine)

if not os.getenv("TESTING"):
    STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def root():
    if os.getenv("TESTING"):
        return {"msg": "OK"}
    STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(400, "Username already exists")
    user = models.User(username=username, password=password)
    db.add(user)
    db.commit()
    return {"msg": "created"}


@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == username,
        models.User.password == password
    ).first()
    if not user:
        raise HTTPException(401, "wrong data")
    token = create_token({"user_id": user.id})
    return {"access_token": token}


@app.post("/tasks")
def create_task(
        title: str,
        description: str = "",
        status: str = "pending",
        priority: int = 0,
        due_date: str = "",
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    task = models.Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        user_id=user.id
    )
    if due_date and due_date.strip():
        try:
            task.due_date = date.fromisoformat(due_date)
        except Exception as e:
            print(f"Error parsing date: {e}")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks/top")
def top_tasks(n: int = 5, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (db.query(models.Task)
            .filter(models.Task.user_id == user.id)
            .filter(models.Task.status != "done")
            .order_by(models.Task.priority.desc())
            .limit(n)
            .all())


@app.get("/tasks")
def get_tasks(
        sort_by: str = "created_date",
        search: str = "",
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    query = db.query(models.Task).filter(models.Task.user_id == user.id)

    if search:
        query = query.filter(
            (models.Task.title.contains(search)) |
            (models.Task.description.contains(search))
        )

    status_order = case(
        (models.Task.status == "done", 1),
        else_=0
    )

    if sort_by == "due_date":
        query = query.order_by(status_order, models.Task.due_date.asc().nulls_last())
    elif sort_by == "title":
        query = query.order_by(status_order, models.Task.title)
    elif sort_by == "priority":
        query = query.order_by(status_order, models.Task.priority.desc())
    elif sort_by == "status":
        query = query.order_by(models.Task.status)
    else:
        query = query.order_by(status_order, models.Task.created_date.desc())

    return query.all()


@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(models.Task).filter_by(id=task_id, user_id=user.id).first()
    if not task:
        raise HTTPException(404, "not found")
    return task


@app.put("/tasks/{task_id}")
def update_task(
        task_id: int,
        title: str = None,
        description: str = None,
        priority: int = None,
        status: str = None,
        due_date: str = None,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    task = db.query(models.Task).filter_by(id=task_id, user_id=user.id).first()
    if not task:
        raise HTTPException(404, "not found")

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if priority is not None:
        task.priority = priority
    if status is not None:
        task.status = status
    if due_date is not None and due_date.strip():
        try:
            task.due_date = date.fromisoformat(due_date)
        except:
            pass

    db.commit()
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = db.query(models.Task).filter_by(id=task_id, user_id=user.id).first()
    if not task:
        raise HTTPException(404, "not found")
    db.delete(task)
    db.commit()
    return {"msg": "deleted"}
