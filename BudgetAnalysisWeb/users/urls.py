from django.urls import path, include
from django.views.generic import TemplateView

from users.views import *

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('login/', MyLoginView.as_view(), name='login'),
    path('register/', Register.as_view(), name='register'),

    path('confirm_email/',
         TemplateView.as_view(template_name='users/registration/confirm_email.html'),
         name='confirm_email'),

    path('verify_email/<uidb64>/<token>/',
         EmailVerify.as_view(),
         name='verify_email'),

    path('invalid_verify/',
         TemplateView.as_view(template_name='users/registration/invalid_verify.html'),
         name='invalid_verify'),

    path('', main, name='main'),
    path('profile/', profile_view, name='profile'),

    path('categories/', category_list, name='category_list'),
    path('categories/create/', category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', category_delete, name='category_delete'),

    path('accounts/', account_list, name='accounts'),
    path('accounts/create/', create_account, name='create_account'),
    path('accounts/<int:account_id>/edit/', edit_account, name='edit_account'),
    path('accounts/delete/<int:account_id>/', delete_account, name='delete_account'),

    path('transfer/', transfer, name='transfer'),

    path('adding/add-operation/', add_operation, name='add_operation'),
    path('adding/edit-operation/<int:operation_id>/', edit_operation, name='edit_operation'),
    path('adding/delete-operation/<int:operation_id>/', delete_operation, name='delete_operation'),
    path('adding/operation-list/', operation_list, name='operation_list'),

    path('adding/add-transaction/', add_regular_transaction, name='add_transaction'),
    path('adding/edit-transaction/<int:transaction_id>/', edit_regular_transaction, name='edit_transaction'),
    path('adding/delete-transaction/<int:transaction_id>/', delete_regular_transaction, name='delete_transaction'),
    path('adding/transaction-list/', regular_transaction_list, name='transaction_list'),

    path('adding/', main_page_for_adding_operation, name='main_for_adding')
]
