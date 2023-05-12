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

    path('accounts/', accounts, name='accounts'),
    path('accounts/create/', create_account, name='create_account'),
    path('accounts/<int:account_id>/edit/', edit_account, name='edit_account'),
    path('accounts/delete/<int:account_id>/', delete_account, name='delete_account'),

    path('transfer/', transfer, name='transfer'),
]
