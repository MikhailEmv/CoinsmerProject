import accounts as accounts
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import (
    UserCreationForm as DjangoUserCreationForm,
    AuthenticationForm as DjangoAuthenticationForm,
)
from django import forms
from django.core.exceptions import ValidationError
from django.forms import Select, TimeInput, DateInput
from django.utils.translation import gettext_lazy as _

from users.models import UserDataModel, CategoryModel, Account, Transaction, Operation, RegularTransaction
from users.utils import send_email_for_verify

User = get_user_model()


class AuthenticationForm(DjangoAuthenticationForm):

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)

            if not self.user_cache.email_verify:
                send_email_for_verify(self.request, self.user_cache)
                raise ValidationError('Ваш почта не верифицирована, проверьте ее', code='invalid_login')

            if self.user_cache is None:
                raise self.get_invalid_login_error()

            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UserCreationFormImpl(DjangoUserCreationForm):

    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserDataModel
        fields = ('name', 'surname', 'patronymic', 'date_of_birth', 'phone', 'sex')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UserProfileForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        user_profile = super().save(commit=False)
        if self.request and self.request.user:
            user_profile.user = self.request.user
        if commit:
            user_profile.save()
        return user_profile


class CategoryForm(forms.ModelForm):
    class Meta:
        model = CategoryModel
        fields = ('category_name', 'key', 'color')
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'balance', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['from_account', 'to_account', 'amount', 'date', 'comment']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ['key', 'category', 'account', 'date', 'amount', 'comment']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }

    def __init__(self, user, *args, **kwargs):
        super(OperationForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = CategoryModel.objects.filter(user=user)
        self.fields['account'].queryset = Account.objects.filter(user=user)


class RegularTransactionForm(forms.ModelForm):
    class Meta:
        model = RegularTransaction
        fields = ['key', 'category', 'amount', 'account', 'date', 'periodicity', 'time_of_notification', 'comment']
        widgets = {
            'category': Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'account': Select(attrs={'class': 'form-control'}),
            'date': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'periodicity': Select(attrs={'class': 'form-control'}),
            'time_of_notification': TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'comment': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = CategoryModel.objects.filter(user=user)
        self.fields['account'].queryset = Account.objects.filter(user=user)


class OperationFilterForm(forms.Form):
    account = forms.ModelChoiceField(queryset=Account.objects.none(), required=False, empty_label="Все счета",)
    period = forms.ChoiceField(choices=RegularTransaction.PERIODICITY_CHOICES)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(user=user)
