import json
import logging
from django.contrib.auth import logout
from .forms import *
from .models import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.hashers import check_password  # Import check_password
from django.utils.dateparse import parse_datetime
from datetime import datetime
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import os
from django.db.models import Q
from datetime import date, timedelta
import calendar
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
import uuid
import functools
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal  # Add this import at the top

# Hardcoded admin credentials
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'VivekVikas'  # Use a secure password in production
}

def home(request):
    return render(request, 'home.html')


# admin login
def admin_login_view(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
                request.session['is_admin'] = True  # Set the session variable
                print("Admin session set")  # Debug statement to confirm
                return redirect('admin_dashboard')
            else:
                form.add_error(None, "Invalid credentials.")
    else:
        form = AdminLoginForm()
    return render(request, 'admin_login.html', {'form': form})

def admin_dashboard(request):
    if not request.session.get('is_admin'):
        return redirect('home')
    notifications = Notification.objects.all().order_by('-created_at')

    return render(request, 'admin_dashboard.html')

logger = logging.getLogger(__name__)
def employee_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # First get the employee
            employee = Employee.objects.get(username=username)

            if password == employee.password:
                # Create or get associated User instance
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': employee.name,
                        'email': employee.email
                    }
                )
                
                # Set session data
                request.session['username'] = employee.username
                request.session['employee_id'] = employee.employee_id
                request.session['is_employee'] = True
                request.session['user_id'] = user.id  # Add this line to store user ID
                
                # Update last login
                employee.last_login = timezone.now()
                employee.save()

                # Get redirect URL from session or default to dashboard
                redirect_url = request.session.get('next', '/employee_dashboard/')
                request.session.pop('next', None)
                
                return JsonResponse({
                    "success": True,
                    "redirect_url": redirect_url
                })
            else:
                logger.warning(f"Invalid password attempt for username: {username}")
                return JsonResponse({"success": False, "error": "Invalid credentials"}, status=401)

        except Employee.DoesNotExist:
            logger.warning(f"Login attempt with non-existent username: {username}")
            return JsonResponse({"success": False, "error": "Invalid credentials"}, status=401)

    return render(request, 'employee_login.html')
# Modify the login_required decorator to work with your custom Employee model

def employee_login_required(function):
    @functools.wraps(function)
    def wrap(request, *args, **kwargs):
        # Check if username exists in session
        username = request.session.get('username')
        if username:
            try:
                # Verify employee exists
                employee = Employee.objects.get(username=username)
                request.user = employee  # Attach employee to request
                return function(request, *args, **kwargs)
            except Employee.DoesNotExist:
                messages.error(request, "Employee session invalid. Please login again.")
        
        # Store the requested URL in session for redirect after login
        next_url = request.get_full_path()
        request.session['next'] = next_url
        return redirect('employee_login')
    return wrap


@csrf_exempt
def save_location(request):
    if request.method == 'POST':
        try:
            # Get employee_id from session
            employee_id = request.session.get('employee_id')
            if not employee_id:
                logger.error("Location save attempted without login")
                return JsonResponse({
                    "success": False, 
                    "error": "Please login first",
                    "redirect_url": '/employee_dashboard/'  # Add redirect URL
                }, status=403)

            # Parse location data
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            # Validate coordinates
            if not all([latitude, longitude]):
                return JsonResponse({
                    "success": False, 
                    "error": "Invalid coordinates"
                }, status=400)

            # Save location
            employee = Employee.objects.get(employee_id=employee_id)
            employee.latitude = latitude
            employee.longitude = longitude
            employee.save()

            return JsonResponse({
                "success": True,
                "message": "Location saved successfully",
                "redirect_url": '/employee_dashboard/'  # Add redirect URL
            })

        except Employee.DoesNotExist:
            logger.error(f"Location save attempted with invalid employee_id: {employee_id}")
            return JsonResponse({
                "success": False, 
                "error": "Invalid session",
                "redirect_url": '/employee_login/'
            }, status=403)

        except json.JSONDecodeError:
            return JsonResponse({
                "success": False, 
                "error": "Invalid JSON data"
            }, status=400)

        except Exception as e:
            logger.error(f"Error saving location: {str(e)}")
            return JsonResponse({
                "success": False, 
                "error": "An error occurred"
            }, status=500)

    return JsonResponse({
        "success": False, 
        "error": "Invalid request method"
    }, status=405)

@employee_login_required
def employee_dashboard(request):
    try:
        employee_id = request.session.get('employee_id')
        if not employee_id:
            return redirect('/employee_login/')
        employee = Employee.objects.get(employee_id=employee_id)
        context = {
            'employee': employee,
        }
        return render(request, 'employee_dashboard.html', context)
        
    except Employee.DoesNotExist:
        request.session.flush()
        return redirect('/employee_login/')
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        request.session.flush()
        return redirect('/employee_login/')
def logout_view(request):
    request.session.flush()
    return redirect('home')
def is_admin(user):
    return user.is_authenticated and user.is_staff

# Employee logout function to save logout time
def employee_logout_view(request):
    try:
        employee_id = request.session.get('employee_id')
        if employee_id:
            employee = Employee.objects.get(employee_id=employee_id)
            employee.office_in_time = None  # Optionally reset login time
            employee.save()
        request.session.flush()  # Clear session
    except Employee.DoesNotExist:
        pass
    return redirect('home')


# View for displaying all employees
def employee_view(request):
    employees = Employee.objects.all()
    return render(request, 'employee.html', {'employees': employees})

# View for creating a new employee
def create_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('employee')  # Redirect back to the employee list
    else:
        form = EmployeeForm()
    return render(request, 'create_employee.html', {'form': form})

# View for editing an employee
def edit_employee(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee')  # Redirect to employee list after saving
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'edit_employee.html', {'form': form})

# View for deleting an employee
def delete_employee(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    employee.delete()
    return redirect('employee')  # Redirect back to the employee list



# notifications
def notifications_view(request):
    notifications = Notification.objects.all().order_by('-created_at')  # Fetch all notifications
    form = NotificationForm()  # Include the form for creation
    return render(request, 'notifications.html', {
        'notifications': notifications,
        'form': form,
        'title': 'Create Notification',
        'button_text': 'Create',
    })

def create_notification(request):
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('notifications_view')  # Redirect to the notification list
    else:
        form = NotificationForm()
    return render(request, 'notifications.html', {
        'form': form,
        'title': 'Create Notification',
        'button_text': 'Create'
    })

def update_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        form = NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            form.save()
            return redirect('notifications_view')  # Redirect to the notification list
    else:
        form = NotificationForm(instance=notification)
    return render(request, 'notifications.html', {
        'form': form,
        'title': 'Edit Notification',
        'button_text': 'Update'
    })

def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        notification.delete()
        return redirect('notifications_view')
    return render(request, 'delete_notification.html', {'notification': notification})

# Handle Demand Requests in Employee Dashboard
@employee_login_required
def handle_demand_employee(request):
    try:
        # Get both employee and user
        username = request.session.get('username')
        user_id = request.session.get('user_id')
        
        employee = Employee.objects.get(username=username)
        user = User.objects.get(id=user_id)
        
        # Now use the user instance for demands
        demands = Demand.objects.filter(employee=user).prefetch_related('proofs', 'bills')

        if request.method == 'POST':
            # Get POST data
            date = request.POST.get('date')
            site_name = request.POST.get('site_name')
            company_name = request.POST.get('company_name')
            amount = request.POST.get('amount')
            description = request.POST.get('description')
            
            # Validate date
            if date:
                try:
                    parsed_date = parse_datetime(date)
                    if not parsed_date:
                        raise ValueError("Invalid date format")
                except ValueError:
                    messages.error(request, "Invalid date format.")
                    return redirect('handle_demand_employee')  # Corrected redirect
            else:
                parsed_date = datetime.now()

            # Validate required fields
            if not all([site_name, company_name, amount, description]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('handle_demand_employee')  # Corrected redirect

            # Convert amount to decimal
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    raise ValueError("Amount must be greater than zero.")
            except ValueError:
                messages.error(request, "Invalid amount. Please enter a valid number greater than zero.")
                return redirect('handle_demand_employee')  # Corrected redirect

            # Create demand
            try:
                Demand.objects.create(
                    employee=user,  # Use user instead of employee
                    site_name=site_name,
                    date=parsed_date,
                    company_name=company_name,
                    amount=amount,
                    description=description,
                )
                messages.success(request, "Demand successfully created.")
            except Exception as e:
                messages.error(request, f"Error creating demand: {str(e)}")
                logger.error(f"Error creating demand for {username}: {str(e)}")

            return redirect('handle_demand_employee')  # Corrected redirect

        return render(request, 'demand.html', {'demands': demands})
        
    except (Employee.DoesNotExist, User.DoesNotExist):
        messages.error(request, "Employee session invalid. Please login again.")
        return redirect('employee_login')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        logger.error(f"Error in handle_demand_employee: {str(e)}")
        return redirect('employee_dashboard')


# Handle Demand Requests in Admin Dashboard

@login_required

@csrf_exempt  # Ensure CSRF protection is enabled in production
def handle_demand_admin(request):
    if not request.user.is_authenticated:
        return redirect(f'/admin-login/?next={request.path}')
    if request.method == 'POST':
        demand_id = request.POST.get('demand_id')
        action = request.POST.get('action')

        if not demand_id or not action:
            return JsonResponse({'status': 'error', 'message': 'Invalid input.'}, status=400)

        demand = get_object_or_404(Demand, id=demand_id)

        if action == 'approve':
            demand.status = 'Approved'
        elif action == 'disapprove':
            demand.status = 'Disapproved'
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)

        demand.save()
        return JsonResponse({
            'status': 'success',
            'message': f'Demand {demand.id} updated to {demand.status}.',
            'demand_status': demand.status
        })

    demands = Demand.objects.prefetch_related('proofs', 'bills').all()
    return render(request, 'demands.html', {'demands': demands})



def upload_proof(request, demand_id):
    if request.method == 'POST':
        demand = get_object_or_404(Demand, id=demand_id)
        proof_file = request.FILES.get('proof_file')

        if proof_file:
            # Use MoneyTransferProof instead of Proof
            proof = MoneyTransferProof.objects.create(
                demand=demand, 
                file_path=proof_file, 
                file_name=proof_file.name
            )
            return JsonResponse({'message': 'Proof uploaded successfully!'})
        
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Upload Bills

@csrf_exempt

def upload_bills(request, demand_id):
    if request.method == 'POST' and 'bills' in request.FILES:
        files = request.FILES.getlist('bills')
        demand = get_object_or_404(Demand, id=demand_id)

        for file in files:
            BillUpload.objects.create(
                demand=demand,
                file_name=file.name,
                file_path=file
            )

        messages.success(request, "Bills uploaded successfully.")
        return redirect('employee_dashboard')

    return redirect('demand')

# View to handle Excel uploads

def upload_excel(request, demand_id):
    if request.method == 'POST' and 'excel_file' in request.FILES:
        excel_file = request.FILES['excel_file']
        
        # Check for correct file type (xls or xlsx)
        if not excel_file.name.endswith(('.xls', '.xlsx')):
            messages.error(request, "Please upload an Excel file.")
            return redirect('employee_dashboard')

        demand = get_object_or_404(Demand, id=demand_id)
        
        # Store the file
        file_name = excel_file.name
        file_path = excel_file

        # You may want to save the file in a designated location on the server
        # For simplicity, we are saving it in the default upload_to directory
        messages.success(request, "Excel file uploaded successfully.")
        return redirect('employee_dashboard')

    return redirect('demand')

def update_demand_status(request, demand_id):
    if request.method == 'POST':
        # Get the status from the POST request
        status = request.POST.get('status')

        # Check if the demand exists
        try:
            demand = Demand.objects.get(id=demand_id)
        except Demand.DoesNotExist:
            return JsonResponse({'error': 'Demand not found'}, status=404)

        # Update the status of the demand
        demand.status = status
        demand.save()

        # Return the updated status in the response
        return JsonResponse({'demand_status': demand.status})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
 
def holiday_list(request):
    # Hardcoded holiday list for 2025 with Occasion and Date in YYYY-MM-DD format
    holidays = [
        {'name': 'New Year', 'date': '2025-01-01', 'occasion': 'Celebration of the New Year'},
        {'name': 'Pongal', 'date': '2025-01-14', 'occasion': 'Harvest Festival'},
        {'name': 'Republic Day', 'date': '2025-01-26', 'occasion': 'Celebration of Indian Republic'},
        {'name': 'Maha Shivaratri', 'date': '2025-03-01', 'occasion': 'Hindu Festival Dedicated to Lord Shiva'},
        {'name': 'Holi', 'date': '2025-03-17', 'occasion': 'Festival of Colors'},
        {'name': 'Good Friday', 'date': '2025-04-18', 'occasion': 'Christian Religious Observance'},
        {'name': 'Independence Day', 'date': '2025-08-15', 'occasion': 'Independence from British Rule'},
        {'name': 'Gandhi Jayanti', 'date': '2025-10-02', 'occasion': 'Birthday of Mahatma Gandhi'},
        {'name': 'Dussehra', 'date': '2025-10-21', 'occasion': 'Victory of Good over Evil'},
        {'name': 'Diwali', 'date': '2025-11-11', 'occasion': 'Festival of Lights'},
        {'name': 'Christmas', 'date': '2025-12-25', 'occasion': 'Birth of Jesus Christ'},
    ]
    
    # Privilege Leaves and Sick Leaves
    pl_count = 13
    sl_count = 12

    return render(request, 'calendar.html', {'holidays': holidays, 'pl_count': pl_count, 'sl_count': sl_count})
@login_required  # Change from @employee_login_required
def daily_update(request, post_id=None):
    try:
        # Get user directly from request instead of session
        employee = request.user
        
        # Initialize post
        post = None
        if post_id:
            post = DailyUpdate.objects.filter(id=post_id, employee=employee).first()
            if not post:
                messages.error(request, "Update not found or access denied.")
                return redirect('daily_update')

        if request.method == 'POST':
            form = DailyUpdateForm(request.POST, instance=post)
            if form.is_valid():
                updated_post = form.save(commit=False)
                updated_post.employee = employee
                updated_post.save()
                messages.success(request, "Update saved successfully.")
                return redirect('daily_update')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = DailyUpdateForm(instance=post)

        # Fetch employee's posts
        employee_posts = DailyUpdate.objects.filter(employee=employee)

        return render(request, 'daily_update.html', {
            'form': form,
            'employee_posts': employee_posts,
            'post': post,
        })
        
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        logger.error(f"Error in daily_update: {str(e)}")
        return redirect('employee_dashboard')
@login_required
def admin_daily_update(request):
    if request.user.is_staff:
        # Admin: Show all posts
        posts = DailyUpdate.objects.all()
    else:
        # Employee: Show their own posts
        posts = DailyUpdate.objects.filter(employee=request.user)

    # Allow employees to create posts
    if not request.user.is_staff and request.method == "POST":
        form = DailyUpdateForm(request.POST)
        if form.is_valid():
            daily_update = form.save(commit=False)
            daily_update.employee = request.user
            daily_update.save()
            return redirect('admin_daily_update')
    else:
        form = DailyUpdateForm() if not request.user.is_staff else None

    return render(request, 'admin_daily_update.html', {'form': form, 'posts': posts})


@login_required
def admin_edit_update(request, update_id):
    post = get_object_or_404(DailyUpdate, id=update_id)

    # Check if the logged-in user is the owner or admin
    if not request.user.is_staff and post.employee != request.user:
        return redirect('admin_daily_update')

    if request.method == "POST":
        form = DailyUpdateForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('admin_daily_update')
    else:
        form = DailyUpdateForm(instance=post)

    return render(request, 'admin_daily_update.html', {'form': form, 'post': post})


@login_required
def admin_delete_update(request, update_id):
    post = get_object_or_404(DailyUpdate, id=update_id)

    # Check if the logged-in user is an admin
    if not request.user.is_staff:
        return redirect('admin_daily_update')

    if request.method == "POST":
        post.delete()
        return redirect('admin_daily_update')

    return redirect('admin_daily_update')


@employee_login_required
def employee_profile_view(request):
    # Initialize request_id at the start
    request_id = uuid.uuid4()  # Unique ID for request correlation

    try:
        # Get employee_id from session
        employee_id = request.session.get('employee_id')
        logger.info(f"[{request_id}] Accessing profile for employee_id: {employee_id}")
        logger.debug(f"[{request_id}] Session data: {dict(request.session)}")

        if not employee_id:
            logger.warning(f"[{request_id}] No employee_id in session")
            messages.error(request, "Please login again")
            return redirect('employee_login')

        # Get employee data
        employee = Employee.objects.get(employee_id=employee_id)
        logger.info(f"[{request_id}] Found employee: {employee.name}")

        # Create context with employee data
        context = {
            'employee': employee,
            'page_title': 'Employee Profile',
        }

        # Log the context for debugging (avoid logging sensitive data)
        logger.debug(f"[{request_id}] Context data prepared for rendering")

        # Render the template with context
        response = render(request, 'employee_profile.html', context)
        logger.debug(f"[{request_id}] Response status: {response.status_code}, Content length: {len(response.content)}")
        
        return response

    except Employee.DoesNotExist:
        logger.error(f"[{request_id}] Employee not found for ID: {employee_id}")
        messages.error(request, "Employee not found")
        return redirect('employee_login')

    except Exception as e:
        logger.error(f"[{request_id}] Error in employee_profile_view: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading your profile")
        return redirect('employee_dashboard')

    
def debug_session_view(request):
    return JsonResponse({
        'session_data': dict(request.session),
        'is_authenticated': request.session.get('is_employee', False),
        'employee_id': request.session.get('employee_id'),
    })
