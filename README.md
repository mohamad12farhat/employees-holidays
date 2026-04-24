# Employee Leave Management System

A web-based leave management system built with Flask, allowing employees to request leave and admins to manage and track requests.

## Features

**Employee**
- Register and log in with email and password
- Request leave with automatic working-day calculation (weekends and Lebanese public holidays excluded)
- View personal leave history and remaining balance (15 days/year)

**Admin**
- Dashboard with live stats — total employees, pending, approved, and rejected requests
- View and manage all leave requests (approve / reject)
- See employee full name and email on each request

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** HTML, vanilla CSS

## How to Run

```bash
# Install dependencies
pip install flask

# Run the app
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

**Default admin credentials:**
- Username: `admin`
- Password: `123`
