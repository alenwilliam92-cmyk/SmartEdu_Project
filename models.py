from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date
from django.core.validators import FileExtensionValidator

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class StudentProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    APPLICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    disability = models.CharField(max_length=100, blank=True)
    performance_score = models.FloatField(default=0)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    disability_certificate = models.FileField(upload_to='disability_certificates/', blank=True, null=True)
    application_status = models.CharField(max_length=10, choices=APPLICATION_STATUS_CHOICES, default='pending')

    def __str__(self):
        disability = f" ({self.disability})" if self.disability else ""
        return f"{self.user.get_full_name() or self.user.username}{disability}"

    @property
    def is_fee_paid(self):
        latest = self.payments.order_by('-date').first()
        return bool(latest and latest.paid)

class TeacherProfile(models.Model):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    QUALIFICATION_CHOICES = (
        ('B.Ed', 'Bachelor of Education'),
        ('M.Ed', 'Master of Education'),
        ('B.Sc', 'Bachelor of Science'),
        ('M.Sc', 'Master of Science'),
        ('B.A', 'Bachelor of Arts'),
        ('M.A', 'Master of Arts'),
        ('PhD', 'Doctor of Philosophy'),
        ('M.Phil', 'Master of Philosophy'),
        ('Other', 'Other'),
    )

    SUBJECT_CHOICES = (
        ('Communication and Language Skills', 'Communication and Language Skills'),
        ('Basic Literacy: Reading and Writing', 'Basic Literacy: Reading and Writing'),
        ('Basic Numeracy and Mathematics', 'Basic Numeracy and Mathematics'),
        ('Social Studies', 'Social Studies'),
        ('Guidance and Counseling', 'Guidance and Counseling'),
        ('Physical Education', 'Physical Education'),
        ('Art', 'Art'),
        ('Music', 'Music'),
        ('History', 'History'),
        ('Geography', 'Geography'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('Visual and Hearing ImpairmentsGuidance', 'Visual and Hearing ImpairmentsGuidance'),
        ('Character and Citizenship Education', 'Character and Citizenship Education'),
        ('Other', 'Other'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    assigned_students = models.ManyToManyField(StudentProfile, blank=True, related_name='assigned_teachers')
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, help_text="Contact phone number")
    highest_qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    subject_specialization = models.CharField(max_length=50, choices=SUBJECT_CHOICES, blank=True)
    certifications = models.TextField(blank=True, help_text="Professional certifications (description, optional)")
    certification_pdf = models.FileField(
        upload_to='certifications/',
        blank=True, null=True,
        validators=[FileExtensionValidator(['pdf'])],
        help_text="Professional certification document (PDF only, optional)"
    )

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"

    def get_age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

class ParentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='parent_profile')
    children = models.ManyToManyField(StudentProfile, related_name='parents')

    def __str__(self):
        return f"Parent: {self.user.username}"

class EducationalGame(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    game_url = models.URLField(max_length=500, blank=True, default="")

    def __str__(self):
        return self.name

class Payment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    payment_id = models.CharField(max_length=100, blank=True)
    order_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        status = "Paid" if self.paid else "Pending"
        return f"Payment: {self.student.user.username} - ₹{self.amount:.2f} ({status})"

class StudentApplication(models.Model):
    APPLICATION_CHOICES = (
        ('leave', 'Leave'),
        ('admission', 'Admission'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    application_type = models.CharField(max_length=20, choices=APPLICATION_CHOICES)
    details = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=(('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')),
        default='pending'
    )
    submit_date = models.DateTimeField(auto_now_add=True)
    decision_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.application_type} ({self.status})"

class Activity(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey('TeacherProfile', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class StudentActivity(models.Model):
    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    teacher_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.activity} for {self.student}"

class GameAssignment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    game = models.ForeignKey(EducationalGame, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    def __str__(self):
        return f"{self.game.name} for {self.student.user.username}"

class Notification(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    activity = models.ForeignKey('StudentActivity', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.message[:30]}"

class ActivitySubmission(models.Model):
    student_activity = models.ForeignKey(StudentActivity, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='activity_submissions/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_activity.student.user.username} - {self.file.name}"

class NotificationSubmission(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    submitted_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    file = models.FileField(upload_to='notification_submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)