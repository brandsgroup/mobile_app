from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import *



class AdminLoginForm(forms.Form):
    username = forms.CharField(label="Admin Username", max_length=30)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class EmployeeLoginForm(forms.Form):
    employee_id = forms.CharField(label="Employee ID", max_length=10)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['subject', 'description']

class AdminResponseForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['admin_response']

class EmployeeLoginForm(forms.Form):
    employee_id = forms.CharField(max_length=255)
    password = forms.CharField(widget=forms.PasswordInput())


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'username', 'password', 'dob', 'phone_number', 'email', 'designation', 'document']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
        }


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'message']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter notification title',
                'class': 'form-input'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Enter notification message',
                'class': 'form-textarea',
                'rows': 4
            }),
        }



class DailyUpdateForm(forms.ModelForm):
    class Meta:
        model = DailyUpdate
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }