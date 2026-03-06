from django.contrib import admin
from django.utils.html import format_html
from.models import CustomUser,StudentProfile,TeacherProfile,ParentProfile,Payment,EducationalGame,StudentApplication,GameAssignment,Notification,NotificationSubmission,ActivitySubmission,StudentActivity,Activity

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(StudentProfile)
admin.site.register(ParentProfile)
admin.site.register(Notification)
admin.site.register(NotificationSubmission)
admin.site.register(ActivitySubmission)
admin.site.register(StudentActivity)
admin.site.register(Activity)

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('get_photo_thumbnail', 'get_full_name', 'get_email', 'phone_number', 'gender', 'highest_qualification', 'years_of_experience', 'subject_specialization', 'get_age')
    list_filter = ('gender', 'highest_qualification', 'subject_specialization', 'years_of_experience', )
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'subject_specialization', 'phone_number', )
    readonly_fields = ('get_photo_preview', 'get_age')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'photo', 'get_photo_preview')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'gender', 'get_age', 'phone_number')
        }),
        
        ('Professional Information', {
            'fields': ('highest_qualification', 'years_of_experience', 'subject_specialization',  'certifications', )
        }),
      
        ('Student Assignments', {
            'fields': ('assigned_students',),
            'classes': ('collapse',)
        })
    )
    
    def get_photo_thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.photo.url)
        return format_html('<div style="width: 40px; height: 40px; background-color: #e5e7eb; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #6b7280;">👤</div>')
    get_photo_thumbnail.short_description = 'Photo'
    
    def get_photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" height="150" style="border-radius: 8px; object-fit: cover;" />', obj.photo.url)
        return format_html('<div style="width: 150px; height: 150px; background-color: #e5e7eb; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #6b7280; font-size: 24px;">👤</div>')
    get_photo_preview.short_description = 'Photo Preview'
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_age(self, obj):
        age = obj.get_age()
        return f"{age} years" if age else "Not specified"
    get_age.short_description = 'Age'

admin.site.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'paid', 'date')
    list_filter = ('paid', 'date')
    search_fields = ('student_user_username',)

admin.site.register(EducationalGame)

admin.site.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'application_type', 'status', 'submit_date')
    list_filter = ('application_type', 'status')
    search_fields = ('student_user_username',)

admin.site.register(GameAssignment)
class GameAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'game', 'assigned_at', 'completed')
    list_filter = ('completed',)