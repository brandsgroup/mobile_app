# Generated by Django 5.0.4 on 2025-01-04 12:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0009_loginlogoutactivity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loginlogoutactivity',
            name='login_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
