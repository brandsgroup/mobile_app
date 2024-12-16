# Generated by Django 5.1.3 on 2024-12-06 10:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employeeprofile',
            options={},
        ),
        migrations.RenameField(
            model_name='employeeprofile',
            old_name='login_time',
            new_name='office_in_time',
        ),
        migrations.RemoveField(
            model_name='employeeprofile',
            name='designation',
        ),
        migrations.RemoveField(
            model_name='employeeprofile',
            name='login_latitude',
        ),
        migrations.RemoveField(
            model_name='employeeprofile',
            name='login_longitude',
        ),
        migrations.RemoveField(
            model_name='employeeprofile',
            name='logout_latitude',
        ),
        migrations.RemoveField(
            model_name='employeeprofile',
            name='logout_longitude',
        ),
        migrations.RemoveField(
            model_name='employeeprofile',
            name='phone_number',
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='is_employee',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='employeeprofile',
            name='password',
            field=models.CharField(default=0, max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='employeeprofile',
            name='employee_id',
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='employeeprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]