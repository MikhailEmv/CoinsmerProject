from django.core.exceptions import ValidationError


def positive_number_validator(value):
    if value < 0:
        raise ValidationError('Значение должно быть положительным числом')
