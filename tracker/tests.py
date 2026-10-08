from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Expense


class TrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ram', password='pass12345!')
        self.other = User.objects.create_user('sita', password='pass12345!')
        self.food = Category.objects.create(user=self.user, name='Food')
        self.bills = Category.objects.create(user=self.user, name='Bills')
        self.client.login(username='ram', password='pass12345!')

    def test_register_creates_default_categories(self):
        self.client.logout()
        r = self.client.post(reverse('register'), {
            'username': 'newbie', 'password1': 'Str0ng-pass-99', 'password2': 'Str0ng-pass-99'})
        self.assertRedirects(r, reverse('dashboard'))
        self.assertEqual(Category.objects.filter(user__username='newbie').count(), 6)

    def test_login_required(self):
        self.client.logout()
        r = self.client.get(reverse('expense_list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r.url)

    def test_crud(self):
        r = self.client.post(reverse('expense_create'), {
            'title': 'Momo', 'amount': '250.50', 'category': self.food.pk, 'date': '2026-10-01', 'note': ''})
        self.assertRedirects(r, reverse('expense_list'))
        e = Expense.objects.get()
        self.assertEqual(e.user, self.user)
        self.client.post(reverse('expense_update', args=[e.pk]), {
            'title': 'Momo plate', 'amount': '300', 'category': self.food.pk, 'date': '2026-10-01', 'note': ''})
        e.refresh_from_db()
        self.assertEqual(e.title, 'Momo plate')
        self.client.post(reverse('expense_delete', args=[e.pk]))
        self.assertEqual(Expense.objects.count(), 0)

    def test_negative_amount_rejected(self):
        r = self.client.post(reverse('expense_create'), {
            'title': 'Bad', 'amount': '-5', 'date': '2026-10-01', 'note': ''})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Expense.objects.count(), 0)

    def test_users_cannot_touch_each_others_data(self):
        theirs = Expense.objects.create(user=self.other, title='Secret', amount=10, date=date(2026, 10, 1))
        self.assertEqual(self.client.get(reverse('expense_update', args=[theirs.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('expense_delete', args=[theirs.pk])).status_code, 404)
        r = self.client.get(reverse('expense_list'))
        self.assertNotContains(r, 'Secret')

    def test_search_filter_pagination_and_total(self):
        for i in range(12):
            Expense.objects.create(user=self.user, title=f'Item {i}', amount=10, category=self.food, date=date(2026, 9, 15))
        Expense.objects.create(user=self.user, title='Rent', amount=5000, category=self.bills, date=date(2026, 10, 2))
        r = self.client.get(reverse('expense_list'))
        self.assertEqual(len(r.context['page']), 5)
        r = self.client.get(reverse('expense_list'), {'q': 'rent'})
        self.assertEqual(r.context['total'], Decimal('5000'))
        r = self.client.get(reverse('expense_list'), {'category': self.food.pk})
        self.assertEqual(r.context['total'], Decimal('120'))
        r = self.client.get(reverse('expense_list'), {'date_from': '2026-10-01', 'date_to': '2026-10-31'})
        self.assertEqual(r.context['page'].paginator.count, 1)
        r = self.client.get(reverse('expense_list'), {'date_from': 'garbage'})
        self.assertEqual(r.status_code, 200)

    def test_dashboard_monthly_and_category_totals(self):
        Expense.objects.create(user=self.user, title='A', amount=100, category=self.food, date=date(2026, 10, 3))
        Expense.objects.create(user=self.user, title='B', amount=300, category=self.bills, date=date(2026, 10, 4))
        Expense.objects.create(user=self.user, title='C', amount=50, category=self.food, date=date(2026, 9, 4))
        r = self.client.get(reverse('dashboard'), {'month': '2026-10'})
        self.assertEqual(r.context['month_total'], Decimal('400'))
        self.assertEqual(r.context['by_category'][0]['name'], 'Bills')
        self.assertEqual(r.context['by_category'][0]['percent'], 75)
        self.assertEqual(self.client.get(reverse('dashboard'), {'month': 'abc'}).status_code, 200)

    def test_duplicate_category_rejected(self):
        self.client.post(reverse('category_list'), {'name': 'food'})
        self.assertEqual(Category.objects.filter(user=self.user, name__iexact='food').count(), 1)

    def test_deleting_category_keeps_expenses(self):
        e = Expense.objects.create(user=self.user, title='A', amount=1, category=self.food, date=date(2026, 10, 3))
        self.client.post(reverse('category_delete', args=[self.food.pk]))
        e.refresh_from_db()
        self.assertIsNone(e.category)
