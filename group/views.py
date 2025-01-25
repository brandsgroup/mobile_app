import json
import logging
from django.contrib.auth import logout
from django.urls import reverse
from geopy.geocoders import Nominatim
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
from django.conf import settings

# Hardcoded admin credentials
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'VivekVikas'  # Use a secure password in production
}

def home(request):
    return render(request, 'home.html')

logger = logging.getLogger(__name__)

# Decorator to enforce admin login
def admin_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('admin_login')}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper

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
    def wrap(request, *args, **kwargs):
        # Check both session and User authentication
        if not request.session.get('employee_id'):
            messages.error(request, "Please log in to continue.")
            return redirect('employee_login')
        return function(request, *args, **kwargs)
    return wrap


@csrf_exempt
def save_location(request):
    if request.method == 'POST':
        try:
            employee_id = request.session.get('employee_id')
            if not employee_id:
                logger.error("Employee ID is missing in session.")
                return JsonResponse({"success": False, "error": "Please login first"}, status=403)

            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if not all([latitude, longitude]):
                logger.error("Invalid coordinates: latitude=%s, longitude=%s", latitude, longitude)
                return JsonResponse({"success": False, "error": "Invalid coordinates"}, status=400)

            employee = Employee.objects.get(employee_id=employee_id)
            login_activity = LoginLogoutActivity(
                employee=employee,
                login_time=timezone.now(),
                login_latitude=latitude,
                login_longitude=longitude,
            )
            login_activity.save()

            logger.info("Login activity recorded for employee_id=%s", employee_id)
            return JsonResponse({"success": True, "message": "Login recorded successfully", "redirect_url": '/employee_dashboard/'})

        except Employee.DoesNotExist:
            logger.error("Employee with ID %s does not exist.", employee_id)
            return JsonResponse({"success": False, "error": "Invalid session", "redirect_url": '/employee_login/'}, status=403)

        except json.JSONDecodeError as e:
            logger.error("JSON decode error: %s", str(e))
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)

        except Exception as e:
            logger.exception("An unexpected error occurred: %s", str(e))
            return JsonResponse({"success": False, "error": f"An error occurred: {str(e)}"}, status=500)

    logger.error("Invalid request method: %s", request.method)
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

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

@csrf_exempt
@require_http_methods(["POST"])

def employee_logout_view(request):
    try:
        # Get employee_id from session
        employee_id = request.session.get('employee_id')
        logger.info(f"Employee ID from session: {employee_id}")
        
        if not employee_id:
            logger.error("No employee_id found in session")
            return JsonResponse({"success": False, "error": "Session not found"}, status=403)
        
        try:
            # Parse request body
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data: {e}")
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)
        
        # Extract and validate coordinates
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        logger.info(f"Received coordinates: lat={latitude}, lon={longitude}")
        
        if not all([latitude, longitude]):
            logger.error("Missing coordinates in request")
            return JsonResponse({"success": False, "error": "Invalid coordinates"}, status=400)
        
        try:
            # Get employee and their active session
            employee = Employee.objects.get(employee_id=employee_id)
            
            login_activity = LoginLogoutActivity.objects.select_for_update().filter(
                employee=employee,
                logout_time__isnull=True
            ).first()
            
            if not login_activity:
                logger.error(f"No active session found for employee {employee_id}")
                return JsonResponse({"success": False, "error": "No active session found"}, status=404)
            
            # Update logout details
            current_time = now()
            login_activity.logout_time = current_time
            login_activity.logout_latitude = float(latitude)
            login_activity.logout_longitude = float(longitude)
            
            # Save changes
            login_activity.save()
            logger.info(f"Logout details saved successfully for employee {employee_id}")
            
            # Clear session at the end
            request.session.flush()
            logger.info(f"Session cleared for employee {employee_id}")
            
            return JsonResponse({
                "success": True,
                "message": "Logout successful",
                "logout_time": current_time.isoformat()
            })
            
        except Employee.DoesNotExist:
            logger.error(f"Employee not found: {employee_id}")
            return JsonResponse({"success": False, "error": "Invalid employee"}, status=404)
        
    except Exception as e:
        logger.exception(f"Unexpected error during logout: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "An unexpected error occurred during logout"
        }, status=500)

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

# @login_required(login_url='/admin-login/')
# @csrf_exempt  # Ensure CSRF protection is enabled in production
def handle_demand_admin(request):
    # if not request.user.is_authenticated:
    #     return redirect(f'/admin-login/?next={request.path}')
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

# Employee dashboard view
@employee_login_required
def daily_update(request, post_id=None):
    try:
        # Get employee from session
        employee_id = request.session.get('employee_id')
        user_id = request.session.get('user_id')
        
        if not user_id:
            messages.error(request, "User session expired. Please login again.")
            return redirect('employee_login')

        # Initialize post as None for new updates
        post = None
        if post_id:
            # Fetch existing post for editing, ensuring it belongs to the current employee
            post = get_object_or_404(DailyUpdate, id=post_id, employee_id=user_id)

        if request.method == 'POST':
            form = DailyUpdateForm(request.POST, instance=post)
            if form.is_valid():
                update = form.save(commit=False)
                update.employee_id = user_id
                update.save()
                
                messages.success(request, 
                    "Update modified successfully!" if post_id else "Daily update submitted successfully!")
                return redirect('daily_update')
        else:
            form = DailyUpdateForm(instance=post)

        # Get only the current employee's posts
        employee_posts = DailyUpdate.objects.filter(
            employee_id=user_id
        ).order_by('-created_at')
        
        context = {
            'form': form,
            'post': post,
            'employee_posts': employee_posts,
        }
        return render(request, 'daily_update.html', context)

    except Exception as e:
        logger.error(f"Error in daily_update view: {str(e)}")
        messages.error(request, "An error occurred. Please try again.")
        return redirect('employee_dashboard')

# @admin_required  # Make sure you have this decorator
def admin_daily_update(request):
    try:
        # Check if the user is an admin based on session variable
        # if not request.session.get('is_admin'):
        #     return redirect(reverse('admin_login'))

        # Fetch updates with related employee info
        posts = DailyUpdate.objects.all().select_related('employee').order_by('-created_at')
        
        context = {
            'posts': posts,  # Changed from 'updates' to 'posts' to match template
        }
        
        # Let's add some logging to debug
        print(f"Number of posts fetched: {posts.count()}")
        for post in posts:
            print(f"Post: {post.subject} by {post.employee}")
            
        return render(request, 'admin_daily_update.html', context)

    except Exception as e:
        # Log the error
        logger.error(f"Error in admin_daily_update: {str(e)}")
        messages.error(request, "An error occurred while loading updates.")
        return redirect(reverse('admin_dashboard'))
@admin_login_required
def admin_edit_update(request, update_id):
    try:
        update = get_object_or_404(DailyUpdate, id=update_id)
        if request.method == 'POST':
            subject = request.POST.get('subject')
            description = request.POST.get('description')
            if subject and description:
                update.subject = subject
                update.description = description
                update.save()
                messages.success(request, "Update modified successfully!")
                return redirect('admin_daily_update')
            else:
                messages.error(request, "Both subject and description are required.")
        return render(request, 'admin_edit_update.html', {'update': update})
    except Exception as e:
        logger.error(f"Error in admin_edit_update: {str(e)}")
        messages.error(request, "An error occurred. Please try again.")
        return redirect('admin_daily_update')

@admin_login_required
def admin_delete_update(request, update_id):
    try:
        update = get_object_or_404(DailyUpdate, id=update_id)
        update.delete()
        messages.success(request, "Update deleted successfully.")
        return redirect('admin_daily_update')
    except Exception as e:
        logger.error(f"Error in admin_delete_update: {str(e)}")
        messages.error(request, "An error occurred. Please try again.")
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


def attendance_view(request):
    activities = LoginLogoutActivity.objects.all()[:20]  # Fetch the first 50 entries

    geolocator = Nominatim(user_agent="my_unique_user_agent")

    # Add location names based on latitude and longitude
    for activity in activities:
        try:
            if activity.login_latitude and activity.login_longitude:
                activity.login_location = geolocator.reverse((activity.login_latitude, activity.login_longitude)).address
            else:
                activity.login_location = "Latitude or Longitude missing"
        except GeocoderTimedOut:
            activity.login_location = "Geocoding timed out"
        except GeocoderQuotaExceeded:
            activity.login_location = "Quota exceeded for geocoding API"
        except Exception as e:
            activity.login_location = f"Geocoding failed: {str(e)}"

    return render(request, 'attendance.html', {'activities': activities})
