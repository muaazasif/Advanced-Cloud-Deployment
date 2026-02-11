from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import Task, TaskCreate, TaskUpdate, TaskFilter, TaskStatus, Priority
from .kafka_producer import kafka_producer
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    start_scheduler()
    yield
    # Shutdown
    # Add any cleanup code here if needed

app = FastAPI(title="Todo Chatbot API", version="1.0.0", lifespan=lifespan)

# Scheduler for reminders
scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

async def check_for_due_tasks():
    """Check for tasks that are due and send reminder events"""
    with next(get_session()) as session:
        # Find tasks that are due within the next 5 minutes and haven't had reminders sent
        now = datetime.utcnow()
        five_minutes_later = now + timedelta(minutes=5)
        
        statement = select(Task).where(
            Task.due_date <= five_minutes_later,
            Task.reminder_sent == False,
            Task.status != TaskStatus.COMPLETED
        )
        results = session.exec(statement)
        due_tasks = results.all()
        
        for task in due_tasks:
            # Mark as reminder sent
            task.reminder_sent = True
            session.add(task)
            
            # Publish reminder event
            reminder_event = {
                'event_type': 'reminder.triggered',
                'task_id': task.id,
                'title': task.title,
                'due_at': task.due_date.isoformat() if task.due_date else None,
                'remind_at': now.isoformat(),
                'user_id': 'default_user',  # In a real app, this would come from auth
                'timestamp': now.isoformat()
            }
            
            await kafka_producer.publish_event('reminders', reminder_event)
    
    session.commit()

@app.get("/")
def read_root():
    return {"message": "Todo Chatbot API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Todo Chatbot API is running"}

@app.get("/tasks/", response_model=List[Task])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    filters: TaskFilter = Depends(),
    db: Session = Depends(get_session)
):
    statement = select(Task)
    
    # Apply filters
    if filters.status:
        statement = statement.where(Task.status == filters.status)
    if filters.priority:
        statement = statement.where(Task.priority == filters.priority)
    if filters.tag:
        statement = statement.where(Task.tags.contains(filters.tag))
    if filters.due_after:
        statement = statement.where(Task.due_date >= filters.due_after)
    if filters.due_before:
        statement = statement.where(Task.due_date <= filters.due_before)
    if filters.search:
        statement = statement.where(Task.title.contains(filters.search) | 
                                   Task.description.contains(filters.search))
    
    # Apply sorting
    if filters.sort_by == "due_date":
        if filters.sort_order == "desc":
            statement = statement.order_by(Task.due_date.desc())
        else:
            statement = statement.order_by(Task.due_date.asc())
    elif filters.sort_by == "priority":
        if filters.sort_order == "desc":
            statement = statement.order_by(Task.priority.desc())
        else:
            statement = statement.order_by(Task.priority.asc())
    elif filters.sort_by == "created_at":
        if filters.sort_order == "desc":
            statement = statement.order_by(Task.created_at.desc())
        else:
            statement = statement.order_by(Task.created_at.asc())
    
    statement = statement.offset(skip).limit(limit)
    tasks = db.exec(statement).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, db: Session = Depends(get_session)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate, db: Session = Depends(get_session)):
    db_task = Task.from_orm(task) if hasattr(Task, 'from_orm') else Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Publish task created event
    event_data = {
        'event_type': 'task.created',
        'task_id': db_task.id,
        'task_data': db_task.dict(),
        'user_id': 'default_user',  # In a real app, this would come from auth
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await kafka_producer.publish_event('task-events', event_data)
    
    return db_task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_session)):
    db_task = db.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    # Update timestamp
    db_task.updated_at = datetime.utcnow()
    
    # If status is being updated to completed, publish completion event
    if 'status' in update_data and update_data['status'] == TaskStatus.COMPLETED:
        db_task.completed_at = datetime.utcnow()
        
        # Publish task completed event
        event_data = {
            'event_type': 'task.completed',
            'task_id': db_task.id,
            'task_data': db_task.dict(),
            'user_id': 'default_user',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await kafka_producer.publish_event('task-events', event_data)
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Publish task updated event
    event_data = {
        'event_type': 'task.updated',
        'task_id': db_task.id,
        'task_data': db_task.dict(),
        'user_id': 'default_user',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await kafka_producer.publish_event('task-events', event_data)
    
    return db_task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_session)):
    db_task = db.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    
    # Publish task deleted event
    event_data = {
        'event_type': 'task.deleted',
        'task_id': task_id,
        'user_id': 'default_user',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await kafka_producer.publish_event('task-events', event_data)
    
    return {"message": "Task deleted successfully"}

@app.post("/tasks/{task_id}/complete")
async def complete_task(task_id: int, db: Session = Depends(get_session)):
    db_task = db.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db_task.status = TaskStatus.COMPLETED
    db_task.completed_at = datetime.utcnow()
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Publish task completed event
    event_data = {
        'event_type': 'task.completed',
        'task_id': db_task.id,
        'task_data': db_task.dict(),
        'user_id': 'default_user',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    await kafka_producer.publish_event('task-events', event_data)
    
    return db_task

# Schedule the reminder checker to run every 5 minutes
scheduler.add_job(check_for_due_tasks, CronTrigger(minute="*/5"))

def main():
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

def dev():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
