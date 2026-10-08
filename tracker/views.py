from datetime import date

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import CategoryForm, ExpenseForm, RegisterForm
from .models import Category, Expense

DEFAULT_CATEGORIES = ['Food', 'Transport', 'Bills', 'Shopping', 'Entertainment', 'Other']


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        Category.objects.bulk_create([Category(user=user, name=n) for n in DEFAULT_CATEGORIES])
        login(request, user)
        messages.success(request, 'Welcome! Your account is ready.')
        return redirect('dashboard')
    return render(request, 'register.html', {'form': form})


@login_required
def dashboard(request):
    today = timezone.localdate()
    try:
        year, month = map(int, request.GET.get('month', '').split('-'))
        start = date(year, month, 1)
    except ValueError:
        start = today.replace(day=1)
    end = date(start.year + 1, 1, 1) if start.month == 12 else date(start.year, start.month + 1, 1)

    all_qs = Expense.objects.filter(user=request.user)
    month_qs = all_qs.filter(date__gte=start, date__lt=end)
    month_total = month_qs.aggregate(t=Sum('amount'))['t'] or 0

    by_category = list(
        month_qs.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    )
    for row in by_category:
        row['name'] = row['category__name'] or 'Uncategorized'
        row['percent'] = round(row['total'] / month_total * 100) if month_total else 0

    # last 6 months trend
    months, y, m = [], today.year, today.month
    for _ in range(6):
        months.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    months.reverse()
    totals = {
        r['m']: r['t']
        for r in all_qs.filter(date__gte=months[0]).annotate(m=TruncMonth('date'))
        .values('m').annotate(t=Sum('amount'))
    }
    trend = [{'label': d.strftime('%b %Y'), 'total': totals.get(d, 0)} for d in months]
    biggest = max((t['total'] for t in trend), default=0)
    for t in trend:
        t['percent'] = round(t['total'] / biggest * 100) if biggest else 0

    context = {
        'month_value': start.strftime('%Y-%m'),
        'month_label': start.strftime('%B %Y'),
        'month_total': month_total,
        'month_count': month_qs.count(),
        'all_time_total': all_qs.aggregate(t=Sum('amount'))['t'] or 0,
        'by_category': by_category,
        'trend': trend,
        'recent': all_qs.select_related('category')[:5],
    }
    return render(request, 'dashboard.html', context)


def _parse(value):
    try:
        return parse_date(value or '')
    except ValueError:
        return None


@login_required
def expense_list(request):
    qs = Expense.objects.filter(user=request.user).select_related('category')
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    date_from = _parse(request.GET.get('date_from'))
    date_to = _parse(request.GET.get('date_to'))

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(note__icontains=q))
    if category.isdigit():
        qs = qs.filter(category_id=category)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    total = qs.aggregate(t=Sum('amount'))['t'] or 0
    page = Paginator(qs, 5).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'expense_list.html', {
        'page': page,
        'total': total,
        'categories': Category.objects.filter(user=request.user),
        'filters': {'q': q, 'category': category,
                    'date_from': request.GET.get('date_from', ''),
                    'date_to': request.GET.get('date_to', '')},
        'querystring': params.urlencode(),
    })


@login_required
def expense_create(request):
    form = ExpenseForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        expense = form.save(commit=False)
        expense.user = request.user
        expense.save()
        messages.success(request, 'Expense added.')
        return redirect('expense_list')
    return render(request, 'form_page.html', {'form': form, 'title': 'Add Expense', 'back': 'expense_list'})


@login_required
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    form = ExpenseForm(request.POST or None, instance=expense, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Expense updated.')
        return redirect('expense_list')
    return render(request, 'form_page.html', {'form': form, 'title': 'Edit Expense', 'back': 'expense_list'})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expense_list')
    return render(request, 'confirm_delete.html', {'object': expense, 'back': 'expense_list'})


@login_required
def category_list(request):
    form = CategoryForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.save()
        messages.success(request, 'Category added.')
        return redirect('category_list')
    categories = Category.objects.filter(user=request.user).annotate(n=Count('expenses'))
    return render(request, 'category_list.html', {'categories': categories, 'form': form})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    form = CategoryForm(request.POST or None, instance=category, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('category_list')
    return render(request, 'form_page.html', {'form': form, 'title': 'Edit Category', 'back': 'category_list'})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted. Its expenses are now "Uncategorized".')
        return redirect('category_list')
    return render(request, 'confirm_delete.html', {'object': category, 'back': 'category_list'})
