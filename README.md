# Expense Tracker (Django)

A simple web app to record daily expenses, organise them into categories, and see where the money goes. Built with Django.

## Features
- **Accounts:** register, log in and log out. Every user sees only their own data.
- **Expenses:** add, view, edit and delete expenses (title, amount, category, date, note).
- **Categories:** add, edit and delete your own categories. Six default ones (Food, Transport, Bills, Shopping, Entertainment, Other) are created when you register.
- **Search and filters:** search by title or note, filter by category and by date range, with the filtered total shown below the table.
- **Pagination:** 5 expenses per page.
- **Dashboard:**
  - pick any month to see its total, number of transactions and top category
  - doughnut chart of category-wise spending with percentages (hover a slice to see what you spent on)
  - bar chart of the last 6 months
  - recent expenses list

## Tech stack
- Python and Django (models, views, templates, forms)
- SQLite database
- Tailwind CSS for the design and Chart.js for the charts

## How to run
    python -m venv venv
    venv\Scripts\activate        # Windows  (Linux/Mac: source venv/bin/activate)
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser   # optional, for /admin/
    python manage.py runserver

Then open http://127.0.0.1:8000/ and log in with the demo account below, or register your own.

## Demo login
- Username: kullu
- Password: demo12345

## Run the tests
    python manage.py test

## Project structure
- tracker/models.py  -> Category, Expense
- tracker/forms.py   -> RegisterForm, ExpenseForm, CategoryForm
- tracker/views.py   -> all pages (every view is login-protected and user-scoped)
- tracker/tests.py   -> automated tests
- templates/         -> Tailwind CSS pages