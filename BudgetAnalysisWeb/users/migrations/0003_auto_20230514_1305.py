# Generated by Django 3.2.18 on 2023-05-14 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_categorymodel_key'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='icon',
        ),
        migrations.RemoveField(
            model_name='categorymodel',
            name='icon',
        ),
        migrations.AddField(
            model_name='account',
            name='color',
            field=models.CharField(default='#000000', max_length=7),
        ),
        migrations.AddField(
            model_name='categorymodel',
            name='color',
            field=models.CharField(default='#000000', max_length=7),
        ),
    ]
