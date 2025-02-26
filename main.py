from fastapi import FastAPI, HTTPException, logger
from typing import List
from schemas import Task, TaskCreate, TaskStatus, Priority
from datetime import datetime

app = FastAPI(title="Task Management API")

tasks = {}
task_id_counter = 1


@app.get("/")
async def root():
    return {"message": "hi there from fast api!"}


@app.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate):
    global task_id_counter
    new_task = Task(id=task_id_counter, **task.model_dump())

    tasks[task_id_counter] = new_task
    task_id_counter += 1
    return new_task


@app.get("/tasks/", response_model=List[Task])
async def read_tasks():
    return list(tasks.values())


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return tasks[task_id]


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: TaskCreate):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    updated_task = Task(id=task_id, **task.model_dump())
    tasks[task_id] = updated_task
    return updated_task


@app.delete("tasks/{task_id}")
async def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    del tasks[task_id]
    return {"message": "Task deleted successfully"}
