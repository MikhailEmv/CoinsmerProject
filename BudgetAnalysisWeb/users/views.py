import base64
from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO

from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator as \
    token_generator
from users.forms import AuthenticationForm, UserCreationFormImpl, UserProfileForm, CategoryForm, TransactionForm, \
    AccountForm, OperationForm, RegularTransactionForm
from users.models import UserDataModel, CategoryModel, Account, Operation, RegularTransaction, Transaction
from users.utils import send_email_for_verify

import matplotlib.pyplot as plt
import pandas as pd
from django.db.models import Sum

User = get_user_model()


class MyLoginView(LoginView):
    form_class = AuthenticationForm


class EmailVerify(View):
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)

        if user is not None and token_generator.check_token(user, token):
            user.email_verify = True
            user.save()
            login(request, user)
            return redirect('main')
        return redirect('invalid_verify')

    @staticmethod
    def get_user(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError,
                User.DoesNotExist, ValidationError):
            user = None
        return user


class Register(View):
    template_name = 'users/registration/register.html'

    def get(self, request):
        context = {
            'form': UserCreationFormImpl()
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = UserCreationFormImpl(request.POST)

        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=password)
            send_email_for_verify(request, user)
            return redirect('confirm_email')
        context = {
            'form': form
        }
        return render(request, self.template_name, context)


def statistics_page(request):
    return render(request, 'users/statistics/statistic_base.html')


def main(request):
    accounts = Account.objects.filter(user=request.user)
    daily_operations = Operation.objects.filter(user=request.user)
    regular_transactions = RegularTransaction.objects.filter(user=request.user)

    # Фильтрация операций по типу (Расходы или Доходы)
    expense_operations_daily = daily_operations.filter(key=Operation.EXPENSES)
    income_operations_daily = daily_operations.filter(key=Operation.INCOME)
    expense_operations_regular = regular_transactions.filter(key=RegularTransaction.EXPENSES)
    income_operations_regular = regular_transactions.filter(key=RegularTransaction.INCOME)

    # Объединение операций по типу (Расходы или Доходы)
    expense_operations = list(expense_operations_daily) + list(expense_operations_regular)
    income_operations = list(income_operations_daily) + list(income_operations_regular)

    combined_operations = list(daily_operations) + list(regular_transactions)
    sorted_operations = reversed(sorted(combined_operations, key=lambda op: op.date))

    # Генерация круговых диаграмм для доходов и расходов
    expense_pie = create_pie_chart(expense_operations)
    income_pie = create_pie_chart(income_operations)

    period = request.GET.get('period')

    # Определение начальной и конечной даты в зависимости от выбранного периода
    today = datetime.today().date()
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=6)
        end_date = today
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        start_date = None
        end_date = None

    # Фильтрация операций по выбранному периоду
    if start_date and end_date:
        daily_operations = daily_operations.filter(date__range=(start_date, end_date))
        regular_transactions = regular_transactions.filter(date__range=(start_date, end_date))

    context = {
        'accounts': accounts,
        'daily_operations': daily_operations,
        'regular_transactions': regular_transactions,
        'sorted_operations': sorted_operations,
        'expense_pie': base64.b64encode(expense_pie).decode('utf-8'),
        'income_pie': base64.b64encode(income_pie).decode('utf-8'),
    }

    return render(request, 'profile/main.html', context=context)


def create_pie_chart(operations):
    amounts = [operation.amount for operation in operations]
    categories = [str(operation.category) for operation in operations]

    # Создание круговой диаграммы
    fig, ax = plt.subplots()
    ax.pie(amounts, labels=categories, autopct='%1.1f%%', radius=0.6)

    plt.tight_layout()

    # Преобразование графика в изображение
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    plt.close(fig)

    # Перемещение указателя в начало потока и чтение данных изображения
    image_stream.seek(0)
    image_data = image_stream.getvalue()

    return image_data


@login_required
def profile_view(request):
    user_profile, created = UserDataModel.objects.get_or_create(user=request.user)
    form = UserProfileForm(instance=user_profile)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    return render(request, 'profile/profile.html', {'form': form})


@login_required
def edit_profile_view(request):
    user_profile, created = UserDataModel.objects.get_or_create(user=request.user)
    form = UserProfileForm(instance=user_profile)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    return render(request, 'profile/edit_profile.html', {'form': form})


@login_required
def category_list(request):
    categories = CategoryModel.objects.filter(user=request.user)
    context = {
        'categories': categories,
    }
    return render(request, 'profile/categories/category_list.html', context)


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    context = {
        'form': form
    }
    return render(request, 'profile/categories/category_form.html', context)


@login_required
def category_edit(request, category_id):
    category = get_object_or_404(CategoryModel, id=category_id, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    context = {
        'form': form,
        'category': category
    }
    return render(request, 'profile/categories/category_form.html', context)


@login_required
def category_delete(request, category_id):
    category = get_object_or_404(CategoryModel, id=category_id, user=request.user)
    category.delete()
    return redirect('category_list')


@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user)
    return render(request, 'profile/accounts/accounts.html', {'accounts': accounts})


def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST, request.FILES)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return redirect('accounts')
    else:
        form = AccountForm()
    return render(request, 'profile/accounts/create_account.html', {'form': form})


def edit_account(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('accounts')
    else:
        form = AccountForm(instance=account)
    return render(request, 'profile/accounts/edit_account.html', {'form': form, 'account': account})


def delete_account(request, account_id):
    account = Account.objects.get(id=account_id)
    account.delete()
    return redirect('accounts')


@login_required
def transfer(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            from_account = form.cleaned_data['from_account']
            to_account = form.cleaned_data['to_account']
            amount = form.cleaned_data['amount']
            date = form.cleaned_data['date']
            comment = form.cleaned_data['comment']
            user = request.user # текущий пользователь
            if from_account.balance >= amount:  # Check if the sender has enough funds
                from_account.balance -= amount
                from_account.save()
                to_account.balance += amount
                to_account.save()
                transaction = form.save(commit=False)
                transaction.user = user
                transaction.save()
                return redirect('accounts')
            else:
                form.add_error('from_account', 'Недостаточно средств на счете для осуществления перевода')
    else:
        form = TransactionForm()
    return render(request, 'profile/accounts/transfer.html', {'form': form})


@login_required
def add_operation(request):
    if request.method == 'POST':
        form = OperationForm(request.user, request.POST)
        if form.is_valid():
            operation = form.save(commit=False)
            operation.user = request.user
            operation.save()
            return redirect('operation_list')
    else:
        form = OperationForm(request.user, initial={'date': timezone.now().date()})
    return render(request, 'users/operations/day-to-day/add_operation.html', {'form': form})


@login_required
def edit_operation(request, operation_id):
    operation = Operation.objects.get(id=operation_id)
    if request.method == 'POST':
        form = OperationForm(request.user, request.POST, instance=operation)
        if form.is_valid():
            operation = form.save(commit=False)
            operation.user = request.user
            operation.save()
            return redirect('operation_list')
    else:
        form = OperationForm(request.user, instance=operation)
    return render(request, 'users/operations/day-to-day/edit_operation.html', {'form': form})


@login_required
def delete_operation(request, operation_id):
    operation = Operation.objects.get(id=operation_id)
    operation.delete()
    return redirect('operation_list')


@login_required
def operation_list(request):
    operations = Operation.objects.filter(user=request.user).order_by('-date')
    return render(request, 'users/operations/day-to-day/operation_list.html', {'operations': operations})


@login_required
def add_regular_transaction(request):
    if request.method == 'POST':
        form = RegularTransactionForm(request.user, request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transaction_list')
    else:
        form = RegularTransactionForm(request.user, initial={'date': timezone.now().date()})
    return render(request, 'users/operations/regular/add_transaction.html', {'form': form})


@login_required
def edit_regular_transaction(request, transaction_id):
    transaction = RegularTransaction.objects.get(id=transaction_id)
    if request.method == 'POST':
        form = RegularTransactionForm(request.user, request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transaction_list')
    else:
        form = RegularTransactionForm(request.user, instance=transaction)
    return render(request, 'users/operations/regular/edit_transaction.html', {'form': form})


@login_required
def delete_regular_transaction(request, transaction_id):
    transaction = RegularTransaction.objects.get(id=transaction_id)
    transaction.delete()
    return redirect('transaction_list')


@login_required
def regular_transaction_list(request):
    transactions = RegularTransaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'users/operations/regular/transaction_list.html', {'transactions': transactions})


def main_page_for_adding_operation(request):
    return render(request, 'users/operations/operation_main.html')
