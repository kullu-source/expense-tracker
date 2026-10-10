# Expense Tracker (Django)

Features: user registration/login, expense CRUD, category CRUD, search, category + date-range filters,
pagination, monthly total, category-wise breakdown, 6-month trend dashboard.

## Run
    python -m venv venv
    venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser   # optional, for /admin/
    python manage.py runserver

Open http://127.0.0.1:8000/ and log in with the demo account below, or register your own.

## Test
    python manage.py test

## Structure
- tracker/models.py  -> Category, Expense
- tracker/forms.py   -> RegisterForm, ExpenseForm, CategoryForm
- tracker/views.py   -> all pages (every view is login-protected and user-scoped)
- templates/         -> Tailwind CSS pages (Chart.js for the dashboard charts)

## Demo Login
- Username: kullu
- Password: demo12345
