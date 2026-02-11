// frontend/src/pages/index.js
import Head from 'next/head';
import { useState, useEffect } from 'react';
import styles from '../styles/Home.module.css';

export default function Home({ tasks }) {
  const [tasksData, setTasksData] = useState(tasks || []);
  const [newTask, setNewTask] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/tasks');
      const data = await response.json();
      setTasksData(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setLoading(false);
    }
  };

  const createTask = async (e) => {
    e.preventDefault();
    if (!newTask.trim()) return;

    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newTask,
          description: '',
          priority: 'medium',
          due_date: null,
          tags: '',
          recurrence_pattern: null,
          recurrence_end_date: null
        }),
      });

      if (response.ok) {
        setNewTask('');
        fetchTasks(); // Refresh tasks
      }
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>Advanced Todo Chatbot</title>
        <meta name="description" content="AI-powered task management system" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Animated Hero Section */}
      <section className={styles.hero}>
        <div className="hero-content">
          <h1 className={styles.title}>
            <span className={styles.highlight}>Advanced</span> Todo Chatbot
          </h1>
          <p className={styles.description}>
            Experience the future of task management with AI-powered intelligence and seamless automation
          </p>
          
          <div className={styles.stats}>
            <div className={styles.statItem}>
              <span className={styles.statNumber}>10K+</span>
              <span className={styles.statLabel}>Tasks Managed</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statNumber}>99.9%</span>
              <span className={styles.statLabel}>Uptime</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statNumber}>24/7</span>
              <span className={styles.statLabel}>Automation</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className={styles.features}>
        <div className={styles.featureGrid}>
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <i className="fas fa-sync-alt"></i>
            </div>
            <h3 className={styles.featureTitle}>Smart Recurring Tasks</h3>
            <p className={styles.featureDesc}>
              Automatically create recurring tasks with intelligent scheduling and pattern recognition.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <i className="fas fa-bell"></i>
            </div>
            <h3 className={styles.featureTitle}>Intelligent Reminders</h3>
            <p className={styles.featureDesc}>
              Get timely notifications with smart algorithms that learn your preferences and habits.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <i className="fas fa-tags"></i>
            </div>
            <h3 className={styles.featureTitle}>Advanced Tagging</h3>
            <p className={styles.featureDesc}>
              Organize tasks with powerful tagging system and smart categorization features.
            </p>
          </div>

          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <i className="fas fa-filter"></i>
            </div>
            <h3 className={styles.featureTitle}>Smart Filtering</h3>
            <p className={styles.featureDesc}>
              Find exactly what you need with advanced search, filter, and sort capabilities.
            </p>
          </div>
        </div>
      </section>

      {/* Task Management Section */}
      <section className={styles.tasksSection}>
        <div className={styles.taskContainer}>
          <h2 className={styles.sectionTitle}>Manage Your Tasks</h2>
          
          <div className={styles.controls}>
            <button className={styles.addBtn} onClick={() => document.getElementById('taskInput').focus()}>
              <i className="fas fa-plus"></i> [ + Add Task ]
            </button>
            <button className={styles.searchBtn}>
              <i className="fas fa-search"></i> [ Search 🔍 ]
            </button>
            <button className={styles.filterBtn}>
              <i className="fas fa-filter"></i> [ Filters ⚡ ]
            </button>
          </div>

          <form onSubmit={createTask} className={styles.taskForm}>
            <input
              id="taskInput"
              type="text"
              value={newTask}
              onChange={(e) => setNewTask(e.target.value)}
              placeholder="Enter a new task..."
              className={styles.taskInput}
            />
            <button type="submit" className={styles.submitButton}>
              <i className="fas fa-plus-circle"></i> Add Task
            </button>
          </form>

          {loading ? (
            <div className={styles.loading}>Loading tasks...</div>
          ) : (
            <div className={styles.tasksList}>
              {tasksData.map((task) => (
                <div key={task.id} className={styles.taskCard}>
                  <div className={styles.taskInfo}>
                    <h3>{task.title}</h3>
                    <p>🏷 Tags: {task.tags || 'No tags'}</p>
                    <p>⚡ Priority: {task.priority}</p>
                    <p>📅 Due: {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}</p>
                    <p>🔁 Recurring: {task.recurrence_pattern || 'None'}</p>
                    <p>⏰ Reminder: {task.reminder_sent ? 'Sent' : 'Pending'}</p>
                  </div>
                  <div className={styles.taskActions}>
                    <button className={styles.completeBtn}>
                      <i className="fas fa-check-circle"></i> [✅ Complete]
                    </button>
                    <button className={styles.editBtn}>
                      <i className="fas fa-edit"></i> [✏ Edit]
                    </button>
                    <button className={styles.deleteBtn}>
                      <i className="fas fa-trash-alt"></i> [🗑 Delete]
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <footer className={styles.footer}>
        <p>Advanced Todo Chatbot &copy; {new Date().getFullYear()} - Powered by AI</p>
      </footer>
    </div>
  );
}

// This gets called on every request
export async function getServerSideProps() {
  try {
    // In a real app, you would fetch from your API
    // For now, returning empty array
    return {
      props: { tasks: [] }
    };
  } catch (error) {
    return {
      props: { tasks: [] }
    };
  }
}