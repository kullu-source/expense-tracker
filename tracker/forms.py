from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Category, Expense


INPUT_CLASSES = (
    'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm '
    'focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'
)


class TailwindMixin:
    def _style(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', INPUT_CLASSES)


class RegisterForm(TailwindMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class ExpenseForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].empty_label = 'Uncategorized'
        self._style()


class CategoryForm(TailwindMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self._style()

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        qs = Category.objects.filter(user=self.user, name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('You already have a category with this name.')
        return name
