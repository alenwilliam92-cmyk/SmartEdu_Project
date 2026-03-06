from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import StudentProfile, Payment, Notification, TeacherProfile, ParentProfile

def send_activity_assigned_email(student_user, activity):
    send_mail(
        subject=f'New Activity Assigned: {activity.title}',
        message=(
            f'Dear {student_user.first_name},'
            f'You have been assigned a new activity on SmartEdu:'
            f'Title: {activity.title}'
            f'Description: {activity.description}'
            f'Due Date: {activity.due_date}'
            f'Please check your dashboard to get started.'
        ),
        from_email='alenwilliam@gmail.com',  # change as needed
        recipient_list=[student_user.email],
        fail_silently=False,
    )


def send_low_performance_email_to_teacher(student):
    """
    Send email to all assigned teachers if performance_score < 50.
    """
    if student.performance_score >= 50:
        return  # No alert needed
    
    teachers = student.assigned_teachers.all()
    if not teachers.exists():
        return
    
    subject = f"Low Performance Alert for {student.user.get_full_name()}"
    html_message = render_to_string('emails/low_performance_teacher.html', {
        'student': student,
        'score': student.performance_score,
    })
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [teacher.user.email for teacher in teachers if teacher.user.email]
    
    if recipient_list:
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
    
    # Optional: Create in-app notification
    for teacher in teachers:
        Notification.objects.create(
            user=teacher.user,
            message=f"Low performance alert for {student.user.get_full_name()} (Score: {student.performance_score})"
        )

def send_pending_fee_email_to_parent(payment):
    """
    Send email to all parents of the student for pending payment.
    """
    if payment.paid:
        return  # Already paid
    
    student = payment.student
    parents = student.parents.all()
    if not parents.exists():
        return
    
    subject = f"Pending Fee Reminder for {student.user.get_full_name()}"
    html_message = render_to_string('emails/pending_fee_parent.html', {
        'student': student,
        'payment': payment,
    })
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [parent.user.email for parent in parents if parent.user.email]
    
    if recipient_list:
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
    
    # Optional: Create in-app notification
    for parent in parents:
        Notification.objects.create(
            user=parent.user,
            message=f"Pending fee of ₹{payment.amount} for {student.user.get_full_name()}"
        )    


def send_low_performance_summary_to_teachers(threshold: float = 30.0) -> dict:
    """
    Send one summary email per teacher listing assigned students with
    performance scores below the given threshold.

    Returns a dict summary with counts.
    """
    teachers = (
        TeacherProfile.objects
        .prefetch_related('assigned_students__user', 'user')
        .all()
    )

    total_teachers_contacted = 0
    total_students_listed = 0

    for teacher in teachers:
        low_students = [
            s for s in teacher.assigned_students.all()
            if (s.performance_score or 0) < threshold
        ]

        if not low_students:
            continue

        recipient_email = getattr(teacher.user, 'email', '') or ''
        if not recipient_email:
            continue

        subject = "Action needed: Students with very low performance"

        lines = [
            f"Dear {teacher.user.get_full_name() or teacher.user.username},",
            "",
            "The following assigned students currently have very low performance (score < "
            f"{int(threshold)}):",
            "",
        ]
        for s in low_students:
            student_name = s.user.get_full_name() or s.user.username
            score_val = s.performance_score or 0
            lines.append(f"- {student_name}: {score_val}")
        lines += [
            "",
            "Please review their progress and take appropriate action (extra support,",
            "additional practice, or contacting parents).",
            "",
            "Regards,",
            "SmartEdu",
        ]

        message = "\n".join(lines)

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        total_teachers_contacted += 1
        total_students_listed += len(low_students)

    return {
        'teachers_contacted': total_teachers_contacted,
        'students_listed': total_students_listed,
    }


def send_pending_fees_to_parents() -> dict:
    """
    Send one email per parent listing each linked student's pending fees.
    Uses Payment.paid=False as pending. Includes amount and a due date
    placeholder if not available.

    Returns a dict summary with counts.
    """
    parents = ParentProfile.objects.prefetch_related('children__user', 'user', 'children__payments').all()

    total_parents_contacted = 0
    total_pending_payments = 0

    for parent in parents:
        pending_lines = []
        child_pending_count = 0

        for child in parent.children.all():
            pending = child.payments.filter(paid=False)
            if not pending.exists():
                continue

            student_name = child.user.get_full_name() or child.user.username
            pending_lines.append(f"{student_name}:")
            for p in pending:
                amount_str = f"₹{p.amount}"
                # Due date not modeled; include placeholder
                due_str = "N/A"
                pending_lines.append(f"  - Pending amount: {amount_str} | Due: {due_str}")
                total_pending_payments += 1
                child_pending_count += 1
            pending_lines.append("")

        if not pending_lines:
            continue

        recipient_email = getattr(parent.user, 'email', '') or ''
        if not recipient_email:
            continue

        subject = "Reminder: Pending fee(s) for your child"
        lines = [
            f"Dear {parent.user.get_full_name() or parent.user.username},",
            "",
            "Our records show pending fee(s) for your linked student(s):",
            "",
            *pending_lines,
            "Please log in to SmartEdu to complete the payment(s) at your earliest convenience.",
            "",
            "If you have already completed the payment, kindly ignore this email.",
            "",
            "Regards,",
            "SmartEdu",
        ]
        message = "\n".join(lines)

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        total_parents_contacted += 1

    return {
        'parents_contacted': total_parents_contacted,
        'pending_payments_listed': total_pending_payments,
    }