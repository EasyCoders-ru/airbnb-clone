# Generated by Django 3.1.1 on 2021-05-15 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_login_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, default='', verbose_name='О себе'),
        ),
        migrations.AlterField(
            model_name='user',
            name='gender',
            field=models.CharField(blank=True, choices=[('мужчина', 'Мужчина'), ('женщина', 'Женщина'), ('другое', 'Другое')], max_length=10, verbose_name='Пол'),
        ),
        migrations.AlterField(
            model_name='user',
            name='superhost',
            field=models.BooleanField(default=False, verbose_name='Суперхост'),
        ),
    ]