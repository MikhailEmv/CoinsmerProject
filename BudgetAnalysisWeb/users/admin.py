from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from users.forms import UserCreationFormImpl
from users.models import UserDataModel, CategoryModel, Account, Transaction, Operation, RegularTransaction

User = get_user_model()


@admin.register(User)
class UserAdminImpl(UserAdmin):

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    add_form = UserCreationFormImpl


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'surname', 'patronymic', 'date_of_birth', 'phone', 'sex']


admin.site.register(UserDataModel, UserProfileAdmin)

admin.site.register(CategoryModel)

admin.site.register(Account)

admin.site.register(Transaction)

admin.site.register(Operation)

admin.site.register(RegularTransaction)
