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

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

# Mount static files if they exist
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    # Return the professional frontend HTML
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Todo Chatbot</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow-x: hidden;
        }

        .container {
            width: 100%;
            max-width: 1200px;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            animation: fadeInDown 1s ease-out;
        }

        .header h1 {
            color: white;
            font-size: 3.5rem;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .header p {
            color: rgba(255,255,255,0.9);
            font-size: 1.2rem;
            max-width: 600px;
            margin: 0 auto;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }

        .feature-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            color: white;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid rgba(255,255,255,0.2);
            animation: float 6s ease-in-out infinite;
        }

        .feature-card:nth-child(2) { animation-delay: 0.5s; }
        .feature-card:nth-child(3) { animation-delay: 1s; }
        .feature-card:nth-child(4) { animation-delay: 1.5s; }

        .feature-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }

        .feature-icon {
            font-size: 3rem;
            margin-bottom: 20px;
            color: #fff;
        }

        .feature-title {
            font-size: 1.5rem;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .feature-desc {
            color: rgba(255,255,255,0.8);
            font-size: 1rem;
            line-height: 1.6;
        }

        .cta-section {
            text-align: center;
            margin-top: 50px;
        }

        .cta-button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 15px 40px;
            border: none;
            border-radius: 50px;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(255,107,107,0.4);
            animation: pulse 2s infinite;
        }

        .cta-button:hover {
            transform: scale(1.05);
            box-shadow: 0 15px 40px rgba(255,107,107,0.6);
        }

        .floating-elements {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        }

        .floating-element {
            position: absolute;
            opacity: 0.1;
            animation: float 8s ease-in-out infinite;
        }

        .floating-element:nth-child(1) { top: 10%; left: 10%; font-size: 4rem; animation-delay: 0s; }
        .floating-element:nth-child(2) { top: 20%; right: 15%; font-size: 3rem; animation-delay: 1s; }
        .floating-element:nth-child(3) { bottom: 15%; left: 20%; font-size: 5rem; animation-delay: 2s; }
        .floating-element:nth-child(4) { bottom: 25%; right: 25%; font-size: 2.5rem; animation-delay: 3s; }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .stats-section {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin: 50px 0;
            text-align: center;
        }

        .stat-item {
            color: white;
            margin: 20px;
            animation: fadeInUp 1s ease-out;
        }

        .stat-number {
            font-size: 3rem;
            font-weight: bold;
            display: block;
        }

        .stat-label {
            font-size: 1rem;
            opacity: 0.8;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.5rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="floating-elements">
        <div class="floating-element"><i class="fas fa-tasks"></i></div>
        <div class="floating-element"><i class="fas fa-bell"></i></div>
        <div class="floating-element"><i class="fas fa-sync-alt"></i></div>
        <div class="floating-element"><i class="fas fa-search"></i></div>
    </div>

    <div class="container">
        <div class="header">
            <h1><i class="fas fa-robot"></i> Advanced Todo Chatbot</h1>
            <p>Experience the future of task management with AI-powered intelligence and seamless automation</p>
        </div>

        <div class="stats-section">
            <div class="stat-item">
                <span class="stat-number">10K+</span>
                <span class="stat-label">Tasks Managed</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">99.9%</span>
                <span class="stat-label">Uptime</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">24/7</span>
                <span class="stat-label">Automation</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">150+</span>
                <span class="stat-label">Features</span>
            </div>
        </div>

        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-sync-alt"></i>
                </div>
                <h3 class="feature-title">Smart Recurring Tasks</h3>
                <p class="feature-desc">Automatically create recurring tasks with intelligent scheduling and pattern recognition.</p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-bell"></i>
                </div>
                <h3 class="feature-title">Intelligent Reminders</h3>
                <p class="feature-desc">Get timely notifications with smart algorithms that learn your preferences and habits.</p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-tags"></i>
                </div>
                <h3 class="feature-title">Advanced Tagging</h3>
                <p class="feature-desc">Organize tasks with powerful tagging system and smart categorization features.</p>
            </div>

            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-filter"></i>
                </div>
                <h3 class="feature-title">Smart Filtering</h3>
                <p class="feature-desc">Find exactly what you need with advanced search, filter, and sort capabilities.</p>
            </div>
        </div>

        <div class="cta-section">
            <button class="cta-button" onclick="alert('Connecting to Todo Chatbot API...')">
                <i class="fas fa-play-circle"></i> Start Managing Tasks
            </button>
        </div>
    </div>

    <script>
        // Add interactive effects
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.feature-card');
            cards.forEach((card, index) => {
                card.style.animationDelay = `${index * 0.2}s`;
            });

            // Add hover effect enhancement
            const buttons = document.querySelectorAll('.cta-button');
            buttons.forEach(button => {
                button.addEventListener('click', () => {
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
                    setTimeout(() => {
                        button.innerHTML = '<i class="fas fa-check-circle"></i> Connected!';
                        button.style.background = 'linear-gradient(45deg, #00b894, #00a085)';
                    }, 2000);
                });
            });

            // Add floating animation to stats
            const stats = document.querySelectorAll('.stat-number');
            stats.forEach(stat => {
                animateValue(stat, 0, parseInt(stat.textContent), 2000);
            });

            function animateValue(element, start, end, duration) {
                let startTimestamp = null;
                const step = (timestamp) => {
                    if (!startTimestamp) startTimestamp = timestamp;
                    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                    const value = Math.floor(progress * (end - start) + start);
                    element.textContent = value + (element.textContent.includes('%') ? '%' : (element.textContent.includes('K+') ? 'K+' : ''));
                    if (progress < 1) {
                        window.requestAnimationFrame(step);
                    }
                };
                window.requestAnimationFrame(step);
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

# Enhanced HTML with delete functionality
@app.get("/app", response_class=HTMLResponse)
def app_interface():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Todo Chatbot - App</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: white;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .task-form {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }

        .form-row {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }

        .form-row .form-group {
            flex: 1;
            margin-bottom: 0;
        }

        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.15);
            color: white;
            font-size: 1rem;
        }

        input::placeholder, textarea::placeholder {
            color: rgba(255,255,255,0.7);
        }

        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-right: 10px;
        }

        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .tasks-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .task-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
            position: relative;
        }

        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .task-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0;
        }

        .task-actions {
            display: flex;
            gap: 5px;
        }

        .task-priority {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .priority-low { background: #00b894; }
        .priority-medium { background: #fdcb6e; color: #333; }
        .priority-high { background: #e17055; }

        .task-description {
            margin: 10px 0;
            color: rgba(255,255,255,0.9);
            line-height: 1.5;
        }

        .task-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid rgba(255,255,255,0.1);
            font-size: 0.9rem;
        }

        .task-status {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
        }

        .status-todo { background: #a29bfe; }
        .status-in-progress { background: #fdcb6e; color: #333; }
        .status-completed { background: #00b894; }

        .delete-btn {
            background: #ff6b6b;
            color: white;
            border: none;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
        }

        .delete-btn:hover {
            background: #ff7675;
            transform: scale(1.1);
        }

        .loading {
            text-align: center;
            padding: 20px;
            font-size: 1.2rem;
        }

        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: rgba(255,255,255,0.7);
        }

        .empty-state i {
            font-size: 3rem;
            margin-bottom: 15px;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-tasks"></i> Advanced Todo Chatbot</h1>
            <p>Manage your tasks with AI-powered intelligence</p>
        </div>

        <div class="task-form">
            <h2><i class="fas fa-plus-circle"></i> Add New Task</h2>
            <div class="form-row">
                <div class="form-group">
                    <label for="title">Title *</label>
                    <input type="text" id="title" placeholder="Enter task title">
                </div>
                <div class="form-group">
                    <label for="priority">Priority</label>
                    <select id="priority">
                        <option value="low">Low</option>
                        <option value="medium" selected>Medium</option>
                        <option value="high">High</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label for="dueDate">Due Date</label>
                    <input type="datetime-local" id="dueDate">
                </div>
                <div class="form-group">
                    <label for="status">Status</label>
                    <select id="status">
                        <option value="todo" selected>To Do</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <textarea id="description" rows="3" placeholder="Enter task description"></textarea>
            </div>
            <div class="form-group">
                <label for="tags">Tags (comma separated)</label>
                <input type="text" id="tags" placeholder="work, urgent, project">
            </div>
            <button class="btn btn-primary" onclick="addTask()">
                <i class="fas fa-plus"></i> Add Task
            </button>
        </div>

        <h2><i class="fas fa-list"></i> Your Tasks</h2>
        <div id="tasksContainer" class="tasks-container">
            <div class="loading">Loading tasks...</div>
        </div>
    </div>

    <script>
        // Load tasks when page loads
        document.addEventListener('DOMContentLoaded', function() {
            loadTasks();
        });

        async function loadTasks() {
            try {
                const response = await fetch('/tasks/');
                const tasks = await response.json();
                
                const container = document.getElementById('tasksContainer');
                
                if (tasks.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <i class="fas fa-inbox"></i>
                            <h3>No tasks yet</h3>
                            <p>Add your first task to get started!</p>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = '';
                
                tasks.forEach(task => {
                    const taskCard = createTaskCard(task);
                    container.appendChild(taskCard);
                });
            } catch (error) {
                console.error('Error loading tasks:', error);
                document.getElementById('tasksContainer').innerHTML = 
                    '<div class="empty-state"><p>Error loading tasks</p></div>';
            }
        }

        function createTaskCard(task) {
            const card = document.createElement('div');
            card.className = 'task-card';
            card.innerHTML = `
                <div class="task-header">
                    <h3 class="task-title">${task.title}</h3>
                    <div class="task-actions">
                        ${task.status !== 'completed' ? 
                          `<button class="btn btn-primary" onclick="completeTask(${task.id})" title="Complete task">
                              <i class="fas fa-check"></i>
                           </button>` : 
                          `<span class="task-status status-completed">Completed</span>`}
                        <button class="delete-btn" onclick="deleteTask(${task.id})" title="Delete task">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="task-priority priority-${task.priority}">
                    ${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)} Priority
                </div>
                ${task.description ? `<p class="task-description">${task.description}</p>` : ''}
                <div class="task-meta">
                    <span class="task-status status-${task.status.replace('_', '-')}">
                        ${task.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span>${task.due_date ? new Date(task.due_date).toLocaleString() : 'No due date'}</span>
                </div>
            `;
            return card;
        }

        async function addTask() {
            const title = document.getElementById('title').value;
            const priority = document.getElementById('priority').value;
            const status = document.getElementById('status').value;
            const description = document.getElementById('description').value;
            const dueDate = document.getElementById('dueDate').value;
            const tags = document.getElementById('tags').value;

            if (!title) {
                alert('Please enter a task title');
                return;
            }

            const taskData = {
                title,
                description: description || undefined,
                priority,
                status,
                due_date: dueDate || undefined,
                tags: tags || undefined
            };

            try {
                const response = await fetch('/tasks/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(taskData)
                });

                if (response.ok) {
                    document.getElementById('title').value = '';
                    document.getElementById('description').value = '';
                    document.getElementById('dueDate').value = '';
                    document.getElementById('tags').value = '';
                    loadTasks();
                    alert('Task added successfully!');
                } else {
                    const error = await response.json();
                    alert('Error adding task: ' + JSON.stringify(error));
                }
            } catch (error) {
                alert('Error adding task: ' + error.message);
            }
        }

        async function deleteTask(taskId) {
            if (!confirm('Are you sure you want to delete this task?')) {
                return;
            }

            try {
                const response = await fetch(`/tasks/${taskId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    loadTasks();
                    alert('Task deleted successfully!');
                } else {
                    const error = await response.json();
                    alert('Error deleting task: ' + JSON.stringify(error));
                }
            } catch (error) {
                alert('Error deleting task: ' + error.message);
            }
        }

        async function completeTask(taskId) {
            if (!confirm('Are you sure you want to mark this task as completed?')) {
                return;
            }

            try {
                const response = await fetch(`/tasks/${taskId}/complete`, {
                    method: 'POST'
                });

                if (response.ok) {
                    loadTasks();
                    alert('Task marked as completed successfully!');
                } else {
                    const error = await response.json();
                    alert('Error completing task: ' + JSON.stringify(error));
                }
            } catch (error) {
                alert('Error completing task: ' + error.message);
            }
        }

        // Allow Enter key to submit task
        document.getElementById('title').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addTask();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

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
