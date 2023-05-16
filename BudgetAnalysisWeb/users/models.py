import os

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.files import File
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save

from BudgetAnalysisWeb.settings import AUTH_USER_MODEL
from users.validators import positive_number_validator


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
    )

    email_verify = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class UserDataModel(models.Model):
    user = models.OneToOneField(AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    patronymic = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    sex = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.name}: {self.user}"


class CategoryModel(models.Model):
    EXPENSES = 'Расходы'
    INCOME = 'Доходы'
    CATEGORY_TYPE_CHOICES = (
        (EXPENSES, 'Расходы'),
        (INCOME, 'Доходы'),
    )
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    category_name = models.CharField(max_length=100, blank=True)
    key = models.CharField(max_length=100, choices=CATEGORY_TYPE_CHOICES, default=EXPENSES, blank=True)
    color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return f"{self.category_name}: {self.user}"


class Account(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    balance = models.DecimalField(max_digits=10, decimal_places=2, validators=[positive_number_validator])
    color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return f"{self.name}"


class Transaction(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_transactions')
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[positive_number_validator])
    date = models.DateField(default=timezone.now, editable=True)
    comment = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.from_account} -> {self.to_account}: {self.amount}"


class Operation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[positive_number_validator])
    date = models.DateField()
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category.category_name} ({self.amount})"


class RegularTransaction(models.Model):
    DAY = 'День'
    WEEK = 'Неделя'
    MONTH = 'Месяц'
    YEAR = 'Год'
    PERIODICITY_CHOICES = (
        (DAY, 'День'),
        (WEEK, 'Неделя'),
        (MONTH, 'Месяц'),
        (YEAR, 'Год'),
    )

    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[positive_number_validator])
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    date = models.DateField()
    periodicity = models.CharField(max_length=10, choices=PERIODICITY_CHOICES, default=DAY)
    time_of_notification = models.TimeField()
    comment = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user}: {self.amount} ({self.category}, {self.account})"


def create_default_categories(sender, instance, created, **kwargs):
    if created:
        if CategoryModel.objects.filter(user=instance).count() == 0:
            default_categories_expenses = [
                {'name': 'Кафе и рестораны', 'color': '#abc270'},
                {'name': 'Одежда и аксессуары', 'color': '#c2a170'},
                {'name': 'Красота и здоровье', 'color': '#8fa1b1'},
                {'name': 'Продукты', 'color': '#b74dac'},
                {'name': 'Все для дома', 'color': '#2b2988'},
                {'name': 'Транспорт', 'color': '#5e876c'},
                {'name': 'Развлечения', 'color': '#7a0c0c'},
                {'name': 'Обязательные платежи', 'color': '#bee12f'},
                {'name': 'Переводы', 'color': '#fda769'},
                {'name': 'Другое', 'color': '#bb73dc'}
            ]
            default_categories_revenues = [
                {'name': 'Зарплата', 'color': '#abc270'},
                {'name': 'Стипендия', 'color': '#c2a170'},
                {'name': 'Социальные выплаты', 'color': '#8fa1b1'},
                {'name': 'Проценты по вкладу', 'color': '#fda769'},
                {'name': 'Переводы', 'color': '#5e047d'},
                {'name': 'Другое', 'color': '#313f42'}
            ]

            for category_data in default_categories_expenses:
                category = CategoryModel(user=instance,
                                         category_name=category_data['name'],
                                         key='Расходы',
                                         color=category_data['color'])
                category.save()

            for category_data in default_categories_revenues:
                category = CategoryModel(user=instance,
                                         category_name=category_data['name'],
                                         key='Доходы',
                                         color=category_data['color'])
                category.save()


post_save.connect(create_default_categories, sender=AUTH_USER_MODEL)
