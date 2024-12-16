from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    
    # Authentication Paths
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('employee_login/', views.employee_login_view, name='employee_login'),
    
    # Admin Dashboard Paths
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
 
    path('admin-dashboard/notifications/', views.notifications_view, name='notifications'),
    path('admin-dashboard/employee/', views.employee_view, name='employee'),
    
    # Logout Paths
    path('logout/', views.logout_view, name='logout'),
    path('employee/logout/', views.employee_logout_view, name='employee_logout'),
    
    # Employee Dashboard
    path('employee_dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('profile/', views.employee_view, name='profile'),
    path('employee_profile/', views.employee_profile_view, name='employee_profile'),
    path('save_location/', views.save_location, name='save_location'),  # Add this line
    

    
    # Employee Management Paths (CRUD)
    path('employee/', views.employee_view, name='employee'),
    path('employee/create/', views.create_employee, name='create_employee'),
    path('employee/edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('employee/delete/<int:employee_id>/', views.delete_employee, name='delete_employee'),
    
    # Notifications Paths
    path('notifications_view', views.notifications_view, name='notifications_view'),
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('notifications/edit/<int:pk>/', views.update_notification, name='update_notification'),
    path('notifications/delete/<int:pk>/', views.delete_notification, name='delete_notification'),
    
    # Demand Paths
    path('demand/', views.handle_demand_employee, name='handle_demand_employee'),  # Make sure this is correct

    path('admin-dashboard/demands/', views.handle_demand_admin, name='handle_demand_admin'),
    path('upload-proof/<int:demand_id>/', views.upload_proof, name='upload_proof'),
    path('upload_bills/<int:demand_id>/', views.upload_bills, name='upload_bills'),
    path('upload_excel/<int:demand_id>/', views.upload_excel, name='upload_excel'),
    path('update-demand-status/<int:demand_id>/', views.update_demand_status, name='update_demand_status'),

    path('calendar/', views.holiday_list, name='calendar'),  # Calendar page URL


    path('daily-update/', views.daily_update, name='daily_update'),  # For new posts
    path('daily-update/<int:post_id>/', views.daily_update, name='daily_update'),  # For editing posts
    path('dashboard/daily-update/', views.admin_daily_update, name='admin_daily_update'),
    path('admin-dashboard/daily-update/', views.admin_daily_update, name='admin_daily_update'),  # Changed from admin/
    path('admin/edit-update/<int:update_id>/', views.admin_edit_update, name='admin_edit_update'),
    path('admin/delete-update/<int:update_id>/', views.admin_delete_update, name='admin_delete_update'),
    
    path('debug-session/', views.debug_session_view, name='debug_session'),



]+ static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

