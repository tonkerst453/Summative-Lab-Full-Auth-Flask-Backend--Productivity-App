# Productivity App Flask Backend

This project provides a secure Flask API for a productivity app with user authentication and private notes.

## Features
- User signup, login, logout, and session-based authentication
- Private notes owned by each authenticated user
- Full CRUD support for notes
- Paginated note listing
- Modular Flask package layout with separate models, routes, and app factory

## Installation
```bash
pip install -r requirements.txt
```

## Database Setup
```bash
python seed.py
```

## Run the app
```bash
python run.py
```

## API Endpoints
- POST /signup: Create a new user account
- POST /login: Log in and start a session
- POST /logout: End the current session
- GET /check_session: Return the current authenticated user
- GET /notes: List paginated notes for the current user
- POST /notes: Create a new note for the current user
- GET /notes/<id>: View one note if it belongs to the current user
- PATCH /notes/<id>: Update one note if it belongs to the current user
- DELETE /notes/<id>: Delete one note if it belongs to the current user
