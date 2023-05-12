from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator as \
    token_generator
from users.forms import AuthenticationForm, UserCreationFormImpl, UserProfileForm, CategoryForm, TransactionForm, \
    AccountForm
from users.models import UserDataModel, CategoryModel, Account
from users.utils import send_email_for_verify

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


def main(request):
    return render(request, 'profile/main.html')


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


def accounts(request):
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
