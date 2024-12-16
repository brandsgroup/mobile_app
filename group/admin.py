from django.contrib import admin
from .models import (
    EmployeeProfile,
    Post,
    Employee,
    Notification,
    Demand,
    MoneyTransferProof,
    BillUpload,
    DailyUpdate
)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_employee', 'employee_id', 'office_in_time', 'logout_time')
    search_fields = ('user__username', 'employee_id')
    list_filter = ('is_employee',)
    ordering = ('user__username',)


# @admin.register(Post)
# class PostAdmin(admin.ModelAdmin):
#     list_display = ('subject', 'employee', 'status', 'created_at', 'updated_at')
#     search_fields = ('subject', 'employee__username')
#     list_filter = ('status', 'created_at', 'updated_at')
#     ordering = ('-created_at',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'username', 'email', 'designation', 'dob')
    search_fields = ('name', 'username', 'email', 'designation')
    ordering = ('name',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)
    ordering = ('-created_at',)


@admin.register(Demand)
class DemandAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'company_name', 'employee', 'status', 'amount', 'date')
    search_fields = ('site_name', 'company_name', 'employee__username', 'status')
    list_filter = ('status', 'date')
    ordering = ('-date',)


@admin.register(MoneyTransferProof)
class MoneyTransferProofAdmin(admin.ModelAdmin):
    list_display = ('demand', 'file_path', 'uploaded_at')
    search_fields = ('demand__site_name', 'demand__company_name')
    ordering = ('-uploaded_at',)


@admin.register(BillUpload)
class BillUploadAdmin(admin.ModelAdmin):
    list_display = ('demand', 'file_path', 'uploaded_at')
    search_fields = ('demand__site_name', 'demand__company_name')
    ordering = ('-uploaded_at',)



class DailyUpdateAdmin(admin.ModelAdmin):
    list_display = ('employee', 'subject', 'date', 'time', 'created_at')
    search_fields = ('employee__username', 'subject', 'description')
    list_filter = ('date',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'date', 'time')

admin.site.register(DailyUpdate, DailyUpdateAdmin)