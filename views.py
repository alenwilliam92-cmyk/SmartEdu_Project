from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from myapp.razorpay_integration import client
import razorpay
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from .ai_helpers import compute_performance_insight  
from .models import (TeacherProfile, StudentProfile, ParentProfile, StudentApplication,
Payment, StudentActivity,GameAssignment,EducationalGame,Notification,CustomUser,NotificationSubmission,ActivitySubmission)
from .forms import (   TeacherCreationForm, TeacherRegistrationForm, StudentProfileForm,
StudentUpdateForm,StudentPerformanceForm,TeacherAssignmentForm,LoginForm,RegisterForm,
ApplicationFilterForm,LinkStudentForm,AssignActivityForm,AssignGameForm,PerformanceAlertForm,
AutomatedEmailForm,EducationalGameForm,TeacherEditForm,ActivitySubmissionForm
)
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .utils import (
    send_activity_assigned_email,
    send_low_performance_summary_to_teachers,
    send_pending_fees_to_parents,
)
from decimal import Decimal
from django.db.models import Q, Count
from django.db import transaction
from django.utils import timezone
from django.template.defaultfilters import timesince


def home(request):
    return render(request, 'home.html')

@login_required(login_url='login')
def admin_dashboard(request):
    # Ensure only admins access this view
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.warning(request, "You do not have permission to access the admin dashboard.")
        return redirect('home')

    # Fetch 10 most recent notifications for this admin
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'admin_dashboard.html', {
        "notifications": notifications
    })

@login_required(login_url='login')
def teacher_dashboard(request):
    if not hasattr(request.user, 'role') or request.user.role != 'teacher':
        messages.warning(request, "You do not have permission to access the teacher dashboard.")
        return redirect('home')
    if not hasattr(request.user, 'teacher_profile'):
        TeacherProfile.objects.create(user=request.user)
    teacher_profile = request.user.teacher_profile
    assigned_students = teacher_profile.assigned_students.select_related('user').all()
    return render(request, 'teacher_dashboard.html', {
        'assigned_students': assigned_students,
        'teacher_profile': teacher_profile,
    })
@login_required(login_url='login')
def student_dashboard(request):
    # Only allow students
    if request.user.role != "student":
        messages.warning(request, "You do not have permission to access the student dashboard.")
        return redirect("home")

    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "You don't have a student profile.")
        return redirect("home")
    if not student.is_fee_paid:
        messages.warning(request, "Please pay your fees to access the dashboard.")
        return redirect('pay_fees')

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]

    return render(request, "student_dashboard.html", {
        "student_data": [student],
        "notifications": notifications,
        "as_parent": False,  # no parent role here
    })
@login_required(login_url='login')
def parent_dashboard(request):
    if not hasattr(request.user, 'role') or request.user.role != 'parent':
        messages.warning(request, "You do not have permission to access the parent dashboard.")
        return redirect('home')
    parent_profile = getattr(request.user, 'parent_profile', None)
    if not parent_profile:
        messages.error(request, "Parent profile not found.")
        return redirect('home')
    children = parent_profile.children.select_related('user').all()
    return render(request, 'parent_dashboard.html', {
        'children': children,
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == "POST":
        subject = request.POST.get("subject")
        email = request.POST.get("email")
        msg = request.POST.get("message")
        # Notify all admins
        admins = CustomUser.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"""Contact Form Submission:
From: {email}
Subject: {subject}
Message:
{msg}"""
            )
        messages.success(request, "Your message has been sent. Thank you!")
        return redirect('thankyou')  
    return render(request, 'contact.html')
def thankyou(request):
    return render(request,'thankyou.html')
def admin_notification(request):
    notifications=Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'admin_notification.html', {'notifications': notifications})
@login_required(login_url='login')
def feedback(request):
    if request.method == "POST":
        feedback_msg = request.POST.get('message', '').strip()  # Change 'feedback' to 'message'
        if not feedback_msg:
            messages.warning(request, "Feedback cannot be empty.")
        else:
            try:
                admin_users = CustomUser.objects.filter(role='admin')
                for admin in admin_users:
                    Notification.objects.create(
                        user=admin,
                        message=f"Parent feedback from {request.user.get_full_name() or request.user.username}: {feedback_msg}"
                    )
                messages.success(request, "Thank you for your feedback! It has been sent to the admin.")
            except Exception as e:
                messages.error(request, f"Could not submit feedback: {e}")
        return redirect('feedback')
    return render(request, 'feedback.html')


def login_view(request):
    # If already authenticated, redirect based on role
    if request.user.is_authenticated:
        role = getattr(request.user, 'role', None)
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'student':
            return redirect('student_dashboard')
        elif role == 'parent':
            return redirect('parent_dashboard')
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        selected_role = request.POST.get('role')
        if form.is_valid():
            user = form.get_user()
            # Check that selected role matches user role
            if getattr(user, 'role', None) == selected_role:
                login(request, user)
                # Redirect according to role
                if selected_role == 'admin':
                    return redirect('admin_dashboard')
                elif selected_role == 'teacher':
                    return redirect('teacher_dashboard')
                elif selected_role == 'student':
                    return redirect('student_dashboard')
                elif selected_role == 'parent':
                    return redirect('parent_dashboard')
                return redirect('home')
            else:
                messages.error(request, "Selected role does not match your account type.")
        else:
            messages.error(request, "Invalid username or password.")
        
        return render(request, 'login.html', {'form': form, 'selected_role': selected_role})
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile upon registration
            if user.role == 'student':
                StudentProfile.objects.create(user=user)
            elif user.role == 'parent':
                ParentProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully. Please login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')

@login_required(login_url='login')
def create_teacher(request):
    """Enhanced teacher creation with detailed profile information"""
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Teacher account created successfully with detailed profile information.')
            return redirect('teacher_list')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'register_teacher.html', {'form': form})

@login_required(login_url='login')
def teacher_list(request):
    teachers = TeacherProfile.objects.select_related('user').all()
    return render(request, 'teacher_list.html', {'teachers': teachers})
@login_required(login_url='login')
def edit_teacher(request, pk):
    teacher_profile = get_object_or_404(TeacherProfile, pk=pk)
    user = teacher_profile.user
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, request.FILES, instance=teacher_profile, user_instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Teacher profile updated successfully.")
            return redirect('teacher_list')
    else:
        form = TeacherEditForm(instance=teacher_profile, user_instance=user)
    return render(request, 'edit_teacher.html', {'form': form})

@login_required(login_url='login')
def delete_teacher(request, pk):
    teacher_profile = get_object_or_404(TeacherProfile, pk=pk)
    user = teacher_profile.user
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Teacher deleted successfully.")
        return redirect('teacher_list')
    return render(request, 'confirm_delete_teacher.html', {'teacher_profile': teacher_profile})

@login_required(login_url='login')
def register_student(request):
    if request.method == 'POST':
        user_form = StudentUpdateForm(request.POST)
        profile_form = StudentProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, "Student account registered successfully.")
            return redirect('parent_dashboard')
    else:
        user_form = StudentUpdateForm()
        profile_form = StudentProfileForm()
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'register_student.html', context)

@login_required(login_url='login')
def student_list(request):
    user = request.user
    # Allow admin to see all students
    if hasattr(user, 'role') and user.role == 'admin':
        students = StudentProfile.objects.select_related('user').all()
    # Teachers see ONLY their assigned students
    elif hasattr(user, 'role') and user.role == 'teacher' and hasattr(user, 'teacher_profile'):
        students = user.teacher_profile.assigned_students.select_related('user').all()
    else:
        # Forbid access for others or show empty list
        students = StudentProfile.objects.none()
    return render(request, 'student_list.html', {'students': students})
@login_required(login_url='login')
def edit_student(request, pk):
    student_profile = get_object_or_404(StudentProfile, pk=pk)
    user = student_profile.user
    if request.method == 'POST':
        user_form = StudentUpdateForm(request.POST, instance=user)
        profile_form = StudentProfileForm(request.POST, request.FILES, instance=student_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Student profile updated successfully.")
            return redirect('parent_dashboard')
    else:
        user_form = StudentUpdateForm(instance=user)
        profile_form = StudentProfileForm(instance=student_profile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'student_profile': student_profile,
    }
    return render(request, 'edit_student.html', context)

@login_required(login_url='login')
def delete_student(request, pk):
    student_profile = get_object_or_404(StudentProfile, pk=pk)
    user = student_profile.user
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect('student_list')
    return render(request, 'confirm_delete_student.html', {'student_profile': student_profile})
@login_required(login_url='login')
def update_performance_score(request, pk):
    # Only allow teachers to update performance
    if not hasattr(request.user, 'role') or request.user.role != 'teacher':
        messages.warning(request, "Only teachers can update performance.")
        return redirect('home')

    student = get_object_or_404(StudentProfile, pk=pk)
    form = StudentPerformanceForm(request.POST or None, instance=student)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Performance score updated!")
            return redirect('student_profile', pk=pk)

    return render(request, 'update_performance_score.html', {'form': form, 'student': student})


@login_required(login_url='login')
def teacher_assignment_list(request):
    # Only show teachers with less than 10 students
    teachers = TeacherProfile.objects.select_related('user').annotate(
        student_count=Count('assigned_students')
    ).filter(student_count__lt=10)
    
    # Add remaining slots to each teacher
    for teacher in teachers:
        teacher.remaining_slots = 10 - teacher.student_count
    
    return render(request, 'teacher_assignment_list.html', {'teachers': teachers})

@login_required(login_url='login')
def assign_students(request, pk):
    teacher_profile = get_object_or_404(TeacherProfile, pk=pk)
    current_student_count = teacher_profile.assigned_students.count()
    max_students = 10

    if current_student_count >= max_students:
        messages.warning(request, f"Teacher {teacher_profile.user.get_full_name()} already has {current_student_count} students assigned. Maximum limit is 10 students per teacher.")
        return redirect('teacher_assignment_list')

    # Pass 'instance' to form so __init__ can filter students
    if request.method == 'POST':
        form = TeacherAssignmentForm(request.POST, instance=teacher_profile)
        if form.is_valid():
            students_to_assign = form.cleaned_data.get('assigned_students', [])
            total_students = len(students_to_assign)
            if total_students > max_students:
                messages.error(request, f"Cannot assign {total_students} students. Max is {max_students}.")
                return render(request, 'assign_students.html', {'form': form, 'teacher_profile': teacher_profile})
            form.save()
            messages.success(request, f"Successfully assigned {total_students} students to {teacher_profile.user.get_full_name()}.")
            return redirect('teacher_assignment_list')
    else:
        form = TeacherAssignmentForm(instance=teacher_profile)

    remaining_slots = max_students - current_student_count
    return render(request, 'assign_students.html', {
        'form': form,
        'teacher_profile': teacher_profile,
        'current_student_count': current_student_count,
        'remaining_slots': remaining_slots,
    })

@login_required(login_url='login')
def monitor_student_applications(request):
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.warning(request, "You do not have permission to access the student applications.")
        return redirect('home')
    applications = StudentApplication.objects.select_related('student__user').order_by('-submit_date')
    filter_form = ApplicationFilterForm(request.GET or None)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        application_type = filter_form.cleaned_data.get('application_type')
        if status:
            applications = applications.filter(status=status)
        if application_type:
            applications = applications.filter(application_type=application_type)
    return render(request, 'monitor_student_applications.html', {
        'applications': applications,
        'filter_form': filter_form,
    })

@login_required(login_url='login')
def student_profile(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    user_role = getattr(request.user, 'role', None)

    # Teacher permissions
    if user_role == 'teacher':
        teacher_profile = getattr(request.user, 'teacher_profile', None)
        if not teacher_profile or student not in teacher_profile.assigned_students.all():
            messages.warning(request, "You do not have permission to view this student profile.")
            return redirect('teacher_dashboard')

    # Student permissions
    elif user_role == 'student':
        if getattr(request.user, 'studentprofile', None) != student:
            messages.warning(request, "You do not have permission to view this profile.")
            return redirect('student_dashboard')

    # Parent permissions
    elif user_role == 'parent':
        parent_profile = getattr(request.user, 'parent_profile', None)
        if not parent_profile or student not in parent_profile.children.all():
            messages.warning(request, "You do not have permission to view this student.")
            return redirect('parent_dashboard')

    # Only admin or allowed roles can pass through
    elif user_role != 'admin':
        messages.warning(request, "You do not have permission to view this profile.")
        return redirect('home')

    # Prefetch activities and related submissions
    student_activities = StudentActivity.objects.filter(student=student).select_related('activity').prefetch_related('submissions')
    parents = student.parents.all() if hasattr(student, 'parents') else []
    teachers = student.assigned_teachers.all() if hasattr(student, 'assigned_teachers') else []
    payments = student.payments.all() if hasattr(student, 'payments') else []

    context = {
        "student": student,
        "parents": parents,
        "teachers": teachers,
        "payments": payments,
        "student_activities": student_activities
    }
    return render(request, "student_profile.html", context)

@login_required(login_url='login')
def pay_fees(request):
    # Only parents can pay fees
    if not hasattr(request.user, 'parent_profile') or request.user.role != 'parent':
        messages.error(request, "Only parents can pay fees.")
        return redirect('home')  # Or your dashboard

    currency = 'INR'
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    fixed_fee = settings.FIXED_STUDENT_FEE

    parent_profile = request.user.parent_profile
    student_choices = parent_profile.children.filter(application_status='accepted').select_related('user')
    selected_student_id = None

    if not student_choices.exists():
        messages.info(request, "No accepted students are available for payment.")

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        selected_student_id = student_id
        student = student_choices.filter(id=student_id).first()
        if not student:
            messages.error(request, "Invalid or ineligible student selected.")
            return render(request, 'pay_fees.html', {'student_choices': student_choices, 'fee': fixed_fee})

        # Already paid check
        if student.payments.filter(paid=True).exists():
            messages.success(request, "Fees already paid for this student.")
            return redirect('pay_fees')

        amount = fixed_fee * 100
        razorpay_order = client.order.create(dict(
            amount=amount,
            currency=currency,
            payment_capture='1'
        ))
        razorpay_order_id = razorpay_order['id']

        context = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': amount,
            'currency': currency,
            'student_choices': student_choices,
            'selected_student_id': student_id,
            'fee': fixed_fee,
            'user': request.user,
        }
        return render(request, 'pay_fees.html', context=context)

    return render(request, 'pay_fees.html', {
        'student_choices': student_choices,
        'fee': fixed_fee,
        'selected_student_id': selected_student_id,
        'user': request.user,
    })

@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        student_id = request.POST.get('student_id')
        amount_rupees = request.POST.get('amount')

        if not (payment_id and razorpay_order_id and signature and student_id and amount_rupees):
            return render(request, 'paymentfail.html', {"error": "Missing payment data."})

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            return render(request, 'paymentfail.html', {"error": "Payment verification failed."})

        student_profile = StudentProfile.objects.filter(id=student_id, application_status='accepted').first()
        if not student_profile:
            return render(request, 'paymentfail.html', {"error": "Student not found or not eligible."})

        Payment.objects.create(
            student=student_profile,
            amount=Decimal(str(amount_rupees)),
            paid=True,
            payment_id=payment_id,
            order_id=razorpay_order_id
        )

        return render(request, 'paymentsuccess.html', {
            "payment_id": payment_id,
            "order_id": razorpay_order_id,
            "amount": amount_rupees
        })
    return redirect('pay_fees')
    
@login_required(login_url='login')
def payment_success(request):
    return render(request, 'paymentsuccess.html')
@login_required(login_url='login')
def all_students_fee_status(request):
    students = StudentProfile.objects.select_related('user').all()
    data = []
    for student in students:
        payments = student.payments.order_by('-date')
        latest_payment = payments.first()
        if latest_payment and latest_payment.paid:
            status = "Paid"
            amount = latest_payment.amount
            date = latest_payment.date
        else:
            status = "Pending"
            amount = "-"
            date = "-"
        data.append({
            'name': student.user.get_full_name(),
            'amount': amount,
            'status': status,
            'date': date,
        })

    paid_count = sum(1 for d in data if d['status'] == "Paid")
    pending_count = sum(1 for d in data if d['status'] == "Pending")

    return render(request, 'students_fee_status.html', {
        "data": data,
        "paid_count": paid_count,
        "pending_count": pending_count,
        "total": len(data)
    })

@login_required(login_url='login')
def student_performance_analysis(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    score = student.performance_score or 0
    ai = compute_performance_insight(score)

    context = {
        "student": student,
        "score": score,
        "ai_label": ai.get("label"),
        "ai_risk": ai.get("risk"),
        "teachers": student.assigned_teachers.all(),
        "parents": student.parents.all() if hasattr(student, 'parents') else [],
    }
    return render(request, "student_performance_analysis.html", context)    

@login_required(login_url='login')
def all_students_performance(request):
    # Optionally restrict to admin:
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
       
        messages.warning(request, "You do not have permission to view this page.")
        return redirect('home')
    students = StudentProfile.objects.select_related('user').all()
    data = []
    for student in students:
        ai = compute_performance_insight(student.performance_score)
        data.append({
            'student': student,
            'score': student.performance_score,
            'ai_label': ai['label'],
            'ai_risk': ai['risk'],
        })
    return render(request, "all_students_performance.html", {"students_data": data})

@login_required(login_url='login')
def teacher_students_performance(request):
    # Ensure only teachers can see this
    if not hasattr(request.user, 'role') or request.user.role != 'teacher':
        
        messages.warning(request, "You do not have permission to view this page.")
        return redirect('home')
    teacher_profile = request.user.teacher_profile
    students = teacher_profile.assigned_students.select_related('user').all()
    table = []
    for student in students:
        ai = compute_performance_insight(student.performance_score)
        table.append({
            'student': student,
            'score': student.performance_score,
            'ai_label': ai['label'],
            'ai_risk': ai['risk'],
        })
    return render(request, "teacher_students_performance.html", {"students_data": table})

@login_required(login_url='login')
def parent_performance_report(request):
    # Make sure only parents can access
    if not hasattr(request.user, 'role') or request.user.role != 'parent':
       
        messages.warning(request, "Access Denied: Only parents can view this page.")
        return redirect('home')
    parent_profile = request.user.parent_profile
    students = parent_profile.children.select_related('user').all()
    table = []
    for student in students:
        ai = compute_performance_insight(student.performance_score)
        table.append({
            'student': student,
            'score': student.performance_score,
            'ai_label': ai['label'],
            'ai_risk': ai['risk'],
        })
    return render(request, "parent_performance_report.html", {"children_data": table})

@login_required(login_url='login')
def link_student_to_parent(request):
    if not hasattr(request.user, 'parent_profile'):
        messages.error(request, "Only parents can link students.")
        return redirect('home')

    parent = request.user.parent_profile

    # Get all students linked to ANY parent
    from myapp.models import ParentProfile
    linked_student_ids = ParentProfile.objects.values_list('children__id', flat=True)

    if request.method == 'POST':
        form = LinkStudentForm(request.POST)
        # Also limit form on POST
        form.fields['student'].queryset = form.fields['student'].queryset.exclude(id__in=linked_student_ids)
        if form.is_valid():
            student = form.cleaned_data['student']
            if student not in parent.children.all():
                parent.children.add(student)
                messages.success(request, f"Linked {student.user.get_full_name()} to your account.")
            else:
                messages.info(request, "This student is already linked.")
            return redirect('parent_dashboard')
    else:
        form = LinkStudentForm()
        form.fields['student'].queryset = form.fields['student'].queryset.exclude(id__in=linked_student_ids)

    return render(request, 'link_student.html', {'form': form})

@login_required(login_url='login')
def play_math_quiz(request):
    return render(request, "games/play_math_quiz.html") 

@login_required(login_url='login')
def play_word_shuffle(request):
    return render(request, "games/play_word_shuffle.html")   

@login_required(login_url='login')
def play_quick_add(request):
    return render(request, "games/play_quick_add.html")  


@login_required(login_url='login')
def educational_games(request):
    
    return render(request, 'games/educational_games.html')




@login_required(login_url='login')
def assign_activity(request):
    teacher_profile = request.user.teacher_profile  # Get current teacher profile
    assigned_students = teacher_profile.assigned_students.select_related('user').all()
    if request.method == 'POST':
        form = AssignActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.created_by = teacher_profile
            activity.save()
            students = form.cleaned_data['students']
            for student in students:
                student_activity = StudentActivity.objects.create(student=student, activity=activity)
                send_activity_assigned_email(student.user, activity)
                Notification.objects.create(
                    user=student.user,
                    message=f'New activity assigned: {activity.title} (Due: {activity.due_date})',
                    activity=student_activity
                )
            return redirect('teacher_dashboard')
    else:
        form = AssignActivityForm()
        form.fields['students'].queryset = assigned_students  # <-- only assigned students

    return render(request, 'assign_activity.html', {'form': form})


@login_required(login_url='login')
def personalized_dashboard(request):
    if not hasattr(request.user, 'role') or request.user.role != 'student':
        messages.warning(request, "You do not have permission to access this dashboard.")
        return redirect('home')
    student = request.user.student_profile
    performance_score = student.performance_score
    # Fetch all assignments for this student
    assignments = GameAssignment.objects.filter(student=student).select_related('game').order_by('-assigned_at')
    # Recommend next game (any game not already assigned)
    played_games = {a.game.pk for a in assignments}
    recommended = EducationalGame.objects.exclude(pk__in=played_games).first()
    context = {
        "student": student,
        "performance_score": performance_score,
        "assignments": assignments,
        "recommended": recommended,
    }
    return render(request, "personalized_dashboard.html", context)

@login_required(login_url='login')
def track_progress(request):
    if not hasattr(request.user, 'role') or request.user.role != 'student':
       
        messages.warning(request, "You do not have permission to view this page.")
        return redirect('home')
    student = request.user.student_profile
    total_games = EducationalGame.objects.count()
    assignments = GameAssignment.objects.filter(student=student).select_related('game')
    completed = assignments.filter(completed=True).count()
    pending = assignments.filter(completed=False).count()
    # Example badges: completed 3 games, completed all assignments
    badges = []
    if completed >= 3:
        badges.append("3 Games Completed")
    if completed == assignments.count() and assignments.exists():
        badges.append("All Assignments Complete")
    context = {
        "student": student,
        "assignments": assignments,
        "completed": completed,
        "pending": pending,
        "total_games": total_games,
        "badges": badges,
    }
    return render(request, "track_progress.html", context)

@csrf_exempt
def update_game_score(request):
    if request.method == "POST" and request.user.is_authenticated:
        data = json.loads(request.body)
        game_name = data.get('game_name')
        score = data.get('score')
        try:
            student = request.user.student_profile
            game = EducationalGame.objects.get(name=game_name)
            assignment = GameAssignment.objects.get(student=student, game=game)
            assignment.completed = True
            assignment.score = score
            assignment.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)})
    return JsonResponse({'status': 'unauthorized'}, status=403)




@login_required(login_url='login')
def assign_game(request):
    teacher_profile = request.user.teacher_profile  # Make sure TeacherProfile exists for this user
    assigned_students = teacher_profile.assigned_students.select_related('user').all()
    if request.method == 'POST':
        form = AssignGameForm(request.POST)
        # Optionally, set queryset here: form.fields['students'].queryset = assigned_students
        if form.is_valid():
            game = form.cleaned_data['game']
            students = form.cleaned_data['students']
            for student in students:
                GameAssignment.objects.create(student=student, game=game)
            messages.success(request, "Game assigned successfully!")
            return redirect('teacher_dashboard')
    else:
        form = AssignGameForm()
        form.fields['students'].queryset = assigned_students  # <-- restrict to only assigned students

    return render(request, 'assign_game.html', {'form': form})

@login_required(login_url='login')
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})
@login_required(login_url='login')
def notification_detail(request, pk, activity_id=None):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    activity = None
    if activity_id:
        try:
            activity = StudentActivity.objects.get(pk=activity_id)
        except StudentActivity.DoesNotExist:
            activity = None

    submission_form = ActivitySubmissionForm()

    if request.method == "POST" and activity:
        submission_form = ActivitySubmissionForm(request.POST, request.FILES)
        print('FILES:', request.FILES)
        print('Form errors:', submission_form.errors)
        if submission_form.is_valid():
            ActivitySubmission.objects.create(
                student_activity=activity,
                file=submission_form.cleaned_data['file']
            )
            messages.success(request, "File uploaded successfully.")
            return redirect('notification_detail', pk=notification.pk, activity_id=activity.pk)
        else:
            messages.error(request, "Upload failed. Please check your file and try again.")

    return render(request, 'notification_detail.html', {
        'notification': notification,
        'activity': activity,
        'submission_form': submission_form
    })

@login_required(login_url='login')
def send_parent_alert(request):
    teacher_profile = getattr(request.user, 'teacher_profile', None)
    if request.method == "POST":
        form = PerformanceAlertForm(request.POST, teacher=teacher_profile)
        if form.is_valid():
            student = form.cleaned_data['student']
            message = form.cleaned_data['message']
            parents = ParentProfile.objects.filter(children=student)
            for parent in parents:
                Notification.objects.create(
                    user=parent.user,
                    message=f"Performance Alert for {student.user.get_full_name()}: {message}"
                )
            return redirect('teacher_dashboard')
    else:
        form = PerformanceAlertForm(teacher=teacher_profile)
    return render(request, 'send_parent_alert.html', {'form': form})


@login_required(login_url='login')
def parent_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "parent_notifications.html", {"notifications": notifications})


@login_required(login_url='login')
def send_automated_emails(request):
    # Admin only
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.warning(request, "You do not have permission to access this page.")
        return redirect('home')

    if request.method == 'POST':
        form = AutomatedEmailForm(request.POST)
        if form.is_valid():
            do_perf = form.cleaned_data.get('send_performance_alerts')
            do_fees = form.cleaned_data.get('send_fee_reminders')

            teachers_contacted = 0
            students_listed = 0
            parents_contacted = 0
            pending_listed = 0

            # Low performance emails per teacher
            if do_perf:
                
                teachers = TeacherProfile.objects.prefetch_related('assigned_students__user', 'user').all()
                for t in teachers:
                    low = [s for s in t.assigned_students.all() if (s.performance_score or 0) < 30]
                    if not low:
                        continue
                    recipient = getattr(t.user, 'email', '') or ''
                    if not recipient:
                        continue
                    subject = "🚨 Low Performance Alert - Action Required"
                    # Build HTML body
                    items = "".join([
                        f"<li><strong>{s.user.get_full_name() or s.user.username}</strong> — Score: {s.performance_score or 0}</li>"
                        for s in low
                    ])
                    html_message = (
                        f"<p>Dear {t.user.get_full_name() or t.user.username},</p>"
                        f"<p>The following assigned students currently have very low performance (score &lt; 30):</p>"
                        f"<ul>{items}</ul>"
                        f"<p><strong>Recommended actions:</strong></p>"
                        f"<ol>"
                        f"<li>Review recent work and identify gaps</li>"
                        f"<li>Assign targeted practice or remedial activities</li>"
                        f"<li>Coordinate with parents for support</li>"
                        f"</ol>"
                        f"<p>Regards,<br/>SmartEdu</p>"
                    )
                    plain_message = (
                        f"Dear {t.user.get_full_name() or t.user.username},\n\n"+
                        "Students with very low performance (score < 30):\n"+
                        "\n".join([
                            f"- {(s.user.get_full_name() or s.user.username)} — Score: {s.performance_score or 0}"
                            for s in low
                        ])+
                        "\n\nRecommended actions:\n"
                        "1) Review recent work and identify gaps\n"
                        "2) Assign targeted practice or remedial activities\n"
                        "3) Coordinate with parents for support\n\n"
                        "Regards,\nSmartEdu"
                    )
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                        recipient_list=[recipient],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    teachers_contacted += 1
                    students_listed += len(low)

            # Pending fee emails per parent
            if do_fees:
                
                parents = ParentProfile.objects.prefetch_related('children__user', 'user', 'children__payments').all()
                for p in parents:
                    pending_sections = []
                    count_for_parent = 0
                    for child in p.children.all():
                        pend = child.payments.filter(paid=False)
                        if not pend.exists():
                            continue
                        list_items = "".join([
                            f"<li>Amount: ₹{pay.amount} | Due: N/A</li>" for pay in pend
                        ])
                        pending_sections.append(
                            f"<p><strong>{child.user.get_full_name() or child.user.username}</strong></p><ul>{list_items}</ul>"
                        )
                        count_for_parent += pend.count()
                    if not pending_sections:
                        continue
                    recipient = getattr(p.user, 'email', '') or ''
                    if not recipient:
                        continue
                    subject = "💰 Fee Payment Reminder"
                    html_message = (
                        f"<p>Dear {p.user.get_full_name() or p.user.username},</p>"
                        f"<p>This is a gentle reminder regarding pending fee(s) for your child(ren) at <strong>SmartEdu</strong>:</p>"
                        + "".join(pending_sections) +
                        f"<p>Please log in to SmartEdu to complete the payment(s) at your earliest convenience.</p>"
                        f"<p>If you have already completed the payment, kindly ignore this email.</p>"
                        f"<p>Regards,<br/>SmartEdu</p>"
                    )
                    plain_message = (
                        f"Dear {p.user.get_full_name() or p.user.username},\n\n"+
                        "Pending fees for your child(ren):\n"+
                        "\n".join([
                            f"{child.user.get_full_name() or child.user.username}: " + ", ".join([f'₹{pay.amount} (Due: N/A)' for pay in child.payments.filter(paid=False)])
                            for child in p.children.all() if child.payments.filter(paid=False).exists()
                        ])+
                        "\n\nPlease log in to SmartEdu to complete the payment(s).\n"
                        "If you have already paid, please ignore this email.\n\n"
                        "Regards,\nSmartEdu"
                    )
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                        recipient_list=[recipient],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    parents_contacted += 1
                    pending_listed += count_for_parent

            if teachers_contacted == 0 and parents_contacted == 0:
                messages.info(request, "No emails to send.")
            else:
                messages.success(
                    request,
                    f"Sent {teachers_contacted} teacher alerts, {parents_contacted} parent reminders"
                )
            return redirect('admin_dashboard')
    else:
        form = AutomatedEmailForm()

    return render(request, 'send_automated_emails.html', {'form': form})

@login_required(login_url='login')
def trigger_teacher_low_performance_emails(request):
    # Restrict to admin
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.warning(request, "You do not have permission to perform this action.")
        return redirect('home')

    summary = send_low_performance_summary_to_teachers(threshold=30.0)

    if summary.get('teachers_contacted', 0) == 0:
        messages.info(request, "No teachers to notify. No students under the threshold.")
    else:
        messages.success(
            request,
            f"Emails sent: {summary['teachers_contacted']} teachers notified about "
            f"{summary['students_listed']} low-performing students."
        )
    return redirect('admin_dashboard')


@login_required(login_url='login')
def trigger_parent_pending_fee_emails(request):
    # Restrict to admin
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.warning(request, "You do not have permission to perform this action.")
        return redirect('home')

    summary = send_pending_fees_to_parents()

    if summary.get('parents_contacted', 0) == 0:
        messages.info(request, "No pending fees found or no parent emails available.")
    else:
        messages.success(
            request,
            f"Emails sent: {summary['parents_contacted']} parents notified about "
            f"{summary['pending_payments_listed']} pending payment(s)."
        )
    return redirect('admin_dashboard')

def admin_game_list(request):
    games = EducationalGame.objects.all().order_by('-id')
    form = EducationalGameForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('admin_game_list')
    return render(request, 'admin_game_list.html', {'games': games, 'form': form})


# Helper functions for admin activity feed
def get_activity_icon(message):
    """Return appropriate icon based on message content"""
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['approved', 'approved']):
        return '✅'
    elif any(keyword in message_lower for keyword in ['rejected', 'deleted', 'banned']):
        return '❌'
    elif any(keyword in message_lower for keyword in ['created', 'assigned', 'linked']):
        return '➕'
    elif any(keyword in message_lower for keyword in ['edited', 'updated']):
        return '✏️'
    elif any(keyword in message_lower for keyword in ['payment', 'fee']):
        return '💰'
    elif any(keyword in message_lower for keyword in ['alert', 'warning']):
        return '⚠️'
    elif message_lower.startswith('contact form'):
        return '📧'
    elif message_lower.startswith('performance alert'):
        return '📊'
    else:
        return '📋'


def get_badge_class(message):
    """Return appropriate badge color class based on message content"""
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['approved']):
        return 'bg-green-100 text-green-800'
    elif any(keyword in message_lower for keyword in ['rejected', 'deleted', 'banned']):
        return 'bg-red-100 text-red-800'
    elif any(keyword in message_lower for keyword in ['created', 'assigned', 'linked']):
        return 'bg-blue-100 text-blue-800'
    elif any(keyword in message_lower for keyword in ['edited', 'updated']):
        return 'bg-blue-100 text-blue-800'
    elif any(keyword in message_lower for keyword in ['payment', 'fee']):
        return 'bg-green-100 text-green-800'
    elif any(keyword in message_lower for keyword in ['alert', 'warning']):
        return 'bg-yellow-100 text-yellow-800'
    elif message_lower.startswith('contact form'):
        return 'bg-purple-100 text-purple-800'
    elif message_lower.startswith('performance alert'):
        return 'bg-yellow-100 text-yellow-800'
    else:
        return 'bg-gray-100 text-gray-800'


@login_required(login_url='login')
def admin_activity_feed(request):
    """
    Admin-only activity feed displaying all admin-related notifications.
    Filters notifications based on admin activity keywords and admin users.
    """
    # Ensure only admins can access this view
    if not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.warning(request, "You do not have permission to access the admin activity feed.")
        return redirect('home')
    
    # Define admin activity keywords
    admin_keywords = [
        'approved', 'rejected', 'deleted', 'created', 'assigned', 
        'payment', 'alert', 'banned', 'edited', 'linked'
    ]
    
    # Build complex query for admin activities
    admin_activities_query = Q()
    
    # Filter by keywords in message
    for keyword in admin_keywords:
        admin_activities_query |= Q(message__icontains=keyword)
    
    # Filter by message prefixes
    admin_activities_query |= Q(message__istartswith='Contact Form')
    admin_activities_query |= Q(message__istartswith='Performance Alert')
    admin_activities_query |= Q(message__istartswith='Fee Payment')
    
    # Filter by admin users (notifications sent to admins)
    admin_users = CustomUser.objects.filter(role='admin')
    admin_activities_query |= Q(user__in=admin_users)
    
    # Get filtered activities ordered by creation date (newest first)
    # Limit to recent activities only (last 50 activities)
    activities = Notification.objects.filter(admin_activities_query).order_by('-created_at')[:50]
    total_count = activities.count()
    
    # Add helper data to each activity
    for activity in activities:
        activity.icon = get_activity_icon(activity.message)
        activity.badge_class = get_badge_class(activity.message)
        activity.relative_time = timesince(activity.created_at)
        # Extract admin name from context if available, else use "System"
        activity.admin_name = getattr(activity.user, 'get_full_name', lambda: 'System')() or 'System'
    
    context = {
        'activities': activities,
        'total_count': total_count,
    }
    
    return render(request, 'admin_activity_feed.html', context)

def student_registration_list(request):
    students = StudentProfile.objects.select_related('user').all().order_by('-id')
    return render(request, 'student_registration_list.html', {
        'student_registrations': students
    })

def accept_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    if request.method == "POST":
        student.application_status = "accepted"
        student.save()
        messages.success(request, f"Student {student.user.get_full_name()} accepted!")
        return redirect('student_registration_list')
    return redirect('student_registration_list')

def reject_student(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    if request.method == "POST":
        student.application_status = "rejected"
        student.save()
        messages.error(request, f"Student {student.user.get_full_name()} rejected!")
        return redirect('student_registration_list')
    return redirect('student_registration_list')

