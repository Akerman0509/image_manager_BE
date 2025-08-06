# 🖼️ Image Manager - Backend

This is the backend server for **Image Manager**, a system that allows users to:

- 📤 Upload and manage images
- 📁 Share folders with other users
- 🔄 Sync individual images or entire folders from cloud storage (e.g., Google Drive)
- 👤 Support **one account connected to multiple cloud drives**

Built with Django, Celery, Redis, and Docker for high scalability and asynchronous task processing.


# Setup Guide

This guide helps you set up and run the backend server for the project.

---

## 🧰 Prerequisites

- Python 3.10+
- Virtualenv (optional but recommended)
- Docker & Docker Compose
- Redis (will be started via Docker)
- PostgreSQL / MySQL / any DB you're using
- `pip` installed

---

## 📦 Step 1: Install Dependencies

Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Install Python packages:

```bash
pip install -r req.txt
```

---

## ⚙️ Step 2: Environment Setup

Update your `.env` file with your database credentials and any other environment variables.

Example `.env`:

```env
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your_secret_key
DEBUG=True
```

> ✅ If you're using MariaDB, it works the same as MySQL for Django.  
> ✅ Make sure your DB user has privileges to create tables and indexes.

---

## 🗃️ Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🐳 Step 4: Start Redis with Docker

Navigate into the Docker folder:

```bash
cd docker
docker compose -f redis.yml up
```

Leave it running in a separate terminal tab or use `-d` to run in background:

```bash
docker compose -f redis.yml up -d
```

---

## 🛰️ Step 5: Run Celery Worker

From the root project directory:

```bash
celery -A image_manager worker --loglevel=info
```

Make sure Redis is running before starting Celery.

---

## 🚀 Step 6: Start Django Server

From the root project directory:

```bash
python manage.py runserver
```

The backend server will be available at:

```
http://localhost:8000/
```

---

## ✅ You're Done!

Your backend is now running and ready to handle requests.