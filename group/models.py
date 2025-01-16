from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from datetime import date, time
from django.utils.timezone import make_aware
from pytz import timezone as pytz_timezone
# Create your models here.

class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_employee = models.BooleanField(default=False)
    employee_id = models.CharField(max_length=20, unique=True)  # Unique ID
    password = models.CharField(max_length=128)
    office_in_time = models.DateTimeField(null=True, blank=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    subject = models.CharField(max_length=255)
    description = models.TextField()
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )
    status_updated_at = models.DateTimeField(null=True, blank=True)
    admin_response = models.TextField(null=True, blank=True)  # Add this field for admin responses

    def __str__(self):
        return f"{self.subject} - {self.status}"

class Employee(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=100)  # No hashing, just plain text password
    dob = models.DateField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    designation = models.CharField(max_length=255)
    document = models.FileField(upload_to='employee_documents/', null=True, blank=True)
    office_in_time = models.DateTimeField(null=True, blank=True)  # To store login time
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # For location tracking
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)  # For location tracking
    is_active = models.BooleanField(default=True)  # To manage employee status
    date_joined = models.DateTimeField(default=now)  # To track when the employee was added to the system
    profile_picture = models.ImageField(upload_to='employee_profiles/', null=True, blank=True)  # Optional profile picture
    last_login = models.DateTimeField(default=timezone.now)  # Add this field

    def __str__(self):
        return self.name



class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    employee = models.ForeignKey(
        User,  # Replace with your Employee model if different
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,  # Set to False if notifications are mandatory for specific users
        blank=True  # Allows notifications for all employees
    )

    def __str__(self):
        return self.title


class Demand(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Disapproved', 'Disapproved'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demands')
    site_name = models.CharField(max_length=255)
    date = models.DateTimeField()
    company_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    class Meta:
        verbose_name = "Demand"
        verbose_name_plural = "Demands"
        ordering = ['-date']  # Latest demand first

    def __str__(self):
        return f"{self.site_name} - {self.company_name}"

    def save(self, *args, **kwargs):
        # Ensure the date is timezone-aware
        if self.date and self.date.tzinfo is None:
            self.date = make_aware(self.date)

        # Validate amount
        if self.amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        super().save(*args, **kwargs)

    
class MoneyTransferProof(models.Model):
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='proofs')
    file_name = models.CharField(max_length=255)  # Save file name for reference
    file_path = models.FileField(upload_to='money_transfer_proofs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} - {self.demand.site_name}"

class BillUpload(models.Model):
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='bills')
    file_name = models.CharField(max_length=255)  # Save file name for reference
    file_path = models.FileField(upload_to='bills/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} - {self.demand.site_name}"
    

class DailyUpdate(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)  # Assuming User model is used for employees
    subject = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)  # Automatically set to today's date on creation
    time = models.TimeField(auto_now_add=True)  # Automatically set to current time on creation
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update by {self.employee.username} on {self.date} at {self.time}"
    

class LoginLogoutActivity(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=now)
    # logout_time = models.DateTimeField(null=True, blank=True)
    login_latitude = models.FloatField()
    login_longitude = models.FloatField()
    # logout_latitude = models.FloatField(null=True, blank=True)
    # logout_longitude = models.FloatField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Convert login_time and logout_time to IST before saving
        ist = pytz_timezone('Asia/Kolkata')
        if not self.login_time:
            self.login_time = now().astimezone(ist)
        else:
            self.login_time = self.login_time.astimezone(ist)

        if self.logout_time:
            self.logout_time = self.logout_time.astimezone(ist)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Activity for {self.employee.employee_id} on {self.login_time}"