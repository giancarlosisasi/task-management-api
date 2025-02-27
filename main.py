from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
import models
import database
import schemas
import security
import auth
from datetime import timedelta
from sqlalchemy.orm import Session

from exceptions import TaskAPIException, task_exception_handler, TaskNotFoundException
from middleware import log_requests_middleware

# load env vars
load_dotenv()


# create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Task Management API")


# Configure CORS
origins = [
    "http://localhost",
    # the backend
    "http://localhost:8080",
    # the frontend
    "http://localhost:3000",
    # any other origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handler
app.add_exception_handler(TaskAPIException, task_exception_handler)

# Add request logging middleware
app.middleware("http")(log_requests_middleware)


# Authentication endpoints
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={
            "sub": user.email,
        },
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/", response_model=List[schemas.User])
async def get_all_users(
    db: Session = Depends(database.get_db),
    _: models.User = Depends(auth.get_current_user),
):
    db_users = db.query(models.User).all()

    return db_users


@app.get("/")
async def root():
    return {"message": "hi there from fast api!"}


@app.get("/tasks/", response_model=List[schemas.Task])
async def read_tasks(db: Session = Depends(database.get_db)):
    tasks = db.query(models.Task).all()
    return tasks


@app.post("/tasks/", response_model=schemas.TaskWithUser)
async def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_task = models.Task(
        title=task.title,
        description=task.title,
        status=models.TaskStatus[task.status.name],
        due_date=task.due_date,
        priority=models.Priority[task.priority.name],
        user_id=current_user.id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@app.get("/tasks/{task_id}", response_model=schemas.Task)
async def read_task(task_id: int, db: Session = Depends(database.get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise TaskNotFoundException(task_id=task_id)
    return task


@app.put("/tasks/{task_id}", response_model=schemas.Task)
async def update_task(
    task_id: int, task: schemas.TaskCreate, db: Session = Depends(database.get_db)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise TaskNotFoundException(task_id=task_id)

    # update attributes
    for key, value in task.model_dump().items():
        print(f"key {key} - value {value}")
        if key in ["status", "priority"] and value is not None:
            # handle enum conversion
            if key == "status":
                value = models.TaskStatus[value.name]
            elif key == "priority":
                value = models.Priority[value.name]

        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(database.get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise TaskNotFoundException(task_id=task_id)

    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
