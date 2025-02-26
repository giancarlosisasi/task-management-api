from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from typing import List
import models, database, schemas
from datetime import datetime
from sqlalchemy.orm import Session

# load env vars
load_dotenv()


# create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Task Management API")


@app.get("/")
async def root():
    return {"message": "hi there from fast api!"}


@app.get("/tasks/", response_model=List[schemas.Task])
async def read_tasks(db: Session = Depends(database.get_db)):
    tasks = db.query(models.Task).all()
    return tasks


@app.post("/tasks/", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, db: Session = Depends(database.get_db)):
    db_task = models.Task(
        title=task.title,
        description=task.title,
        status=models.TaskStatus[task.status.name],
        due_date=task.due_date,
        priority=models.Priority[task.priority.name],
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@app.get("/tasks/{task_id}", response_model=schemas.Task)
async def read_task(task_id: int, db: Session = Depends(database.get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=schemas.Task)
async def update_task(
    task_id: int, task: schemas.TaskCreate, db: Session = Depends(database.get_db)
):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

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
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}
