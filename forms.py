from django import forms
from django.db.models import Q
from .models import CustomUser, StudentProfile, TeacherProfile,StudentApplication,Activity,GameAssignment,EducationalGame,ActivitySubmission,NotificationSubmission
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class TeacherCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'teacher'
        if commit:
            user.save()
        return user

class TeacherRegistrationForm(forms.ModelForm):
    """Enhanced teacher registration form with profile details and PDF certification upload."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        }),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        }),
        help_text="Enter the same password as before, for verification."
    )

    # TeacherProfile fields
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'onchange': 'previewImage(this)'
        }),
        help_text="Upload a profile photo (optional)"
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Select your date of birth (optional)"
    )
    gender = forms.ChoiceField(
        choices=TeacherProfile.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Select your gender (optional)"
    )
    highest_qualification = forms.ChoiceField(
        choices=TeacherProfile.QUALIFICATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Select your highest qualification (optional)"
    )
    years_of_experience = forms.IntegerField(
        initial=0,
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Years of experience'
        }),
        help_text="Enter your years of teaching experience"
    )
    subject_specialization = forms.ChoiceField(
        choices=TeacherProfile.SUBJECT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Select your subject specialization (optional)"
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number'
        }),
        help_text="Contact phone number"
    )
    certifications = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Professional certifications'
        }),
        help_text="List your professional certifications"
    )

    # NEW: Certification PDF field
    certification_pdf = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf'
        }),
        help_text="Upload professional certification PDF (optional)"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords don't match.")
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_certification_pdf(self):
        pdf = self.cleaned_data.get('certification_pdf')
        if pdf and pdf.content_type != 'application/pdf':
            raise ValidationError("Only PDF files are allowed for certifications.")
        return pdf

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'teacher'
        if commit:
            user.save()
            TeacherProfile.objects.create(
                user=user,
                photo=self.cleaned_data.get('photo'),
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                gender=self.cleaned_data.get('gender'),
                phone_number=self.cleaned_data.get('phone_number'),
                highest_qualification=self.cleaned_data.get('highest_qualification'),
                years_of_experience=self.cleaned_data.get('years_of_experience', 0),
                subject_specialization=self.cleaned_data.get('subject_specialization'),
                certifications=self.cleaned_data.get('certifications'),
                certification_pdf=self.cleaned_data.get('certification_pdf'),  # new field
            )
        return user
class StudentCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'student'
        if commit:
            user.save()
        return user

class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['disability', 'photo', 'age', 'gender', 'disability_certificate']
        widgets = {
            'disability': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter disability if any'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }
        
class StudentPerformanceForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['performance_score']
        widgets = {
            'performance_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 0, 'max': 100}),
        }



class TeacherEditForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(max_length=30)
    last_name  = forms.CharField(max_length=30)
    email      = forms.EmailField()
    username   = forms.CharField(max_length=30)
    # Now all TeacherProfile fields...

    class Meta:
        model = TeacherProfile
        fields = [
            'photo', 'date_of_birth', 'gender', 'phone_number', 'highest_qualification',
            'years_of_experience', 'subject_specialization', 'certifications',
            'certification_pdf'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # Set widget classes for other fields as appropriate
        }

    def __init__(self, *args, user_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user_instance is not None:
            self.fields['first_name'].initial = user_instance.first_name
            self.fields['last_name'].initial  = user_instance.last_name
            self.fields['email'].initial      = user_instance.email
            self.fields['username'].initial   = user_instance.username
        self.user_instance = user_instance

    def save(self, commit=True):
        profile = super().save(commit=False)
        # save User fields
        user = self.user_instance
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.username   = self.cleaned_data['username']
        if commit:
            user.save()
            profile.user = user
            profile.save()
            self.save_m2m()
        return profile
class TeacherAssignmentForm(forms.ModelForm):
    assigned_students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': 10,
            'style': 'height: 180px;',
        }),
        required=False,
        label="Assigned Students",
        help_text="Select students to assign to this teacher (maximum 10 students per teacher)"
    )

    class Meta:
        model = TeacherProfile
        fields = ['assigned_students']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk:
            # Find all students already assigned to any other teacher
            assigned_to_others = StudentProfile.objects.filter(
                assigned_teachers__isnull=False
            ).exclude(assigned_teachers=instance)
            # The queryset is: unassigned OR already assigned here
            qs = StudentProfile.objects.exclude(
                id__in=assigned_to_others.values_list('id', flat=True)
            )
            self.fields['assigned_students'].queryset = qs
            current_count = instance.assigned_students.count()
            remaining = 10 - current_count
            self.fields['assigned_students'].help_text = (
                f"Teacher has {current_count} student(s). "
                f"<strong>{remaining} slot(s)</strong> remaining."
            )
        else:
            # Brand new teacher: show only unassigned students
            self.fields['assigned_students'].queryset = StudentProfile.objects.filter(assigned_teachers__isnull=True)

    def clean_assigned_students(self):
        selected = self.cleaned_data.get('assigned_students', [])
        if not self.instance or not self.instance.pk:
            return selected
        new_count = len(selected)
        if new_count > 10:
            raise forms.ValidationError("You cannot assign more than 10 students to a teacher.")
        return selected
    
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user 


class StudentApplicationForm(forms.ModelForm):
    class Meta:
        model = StudentApplication
        fields = ['application_type', 'details']
        widgets = {
            'application_type': forms.Select(attrs={'class': 'form-control'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ApplicationFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All'), ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        required=False, widget=forms.Select(attrs={'class': 'form-control'})
    )
    application_type = forms.ChoiceField(
        choices=[('', 'All'), ('leave', 'Leave'), ('admission', 'Admission')],
        required=False, widget=forms.Select(attrs={'class': 'form-control'})
    )            

class LinkStudentForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=StudentProfile.objects.select_related('user').all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AssignActivityForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Activity
        fields = ['title', 'description', 'due_date', 'students']



class ActivitySubmissionForm(forms.ModelForm):
    class Meta:
        model = ActivitySubmission
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': 'audio/*,video/*,application/pdf,image/*'})
        }
class GameAssignmentForm(forms.ModelForm):
    class Meta:
        model = GameAssignment
        fields = ['student', 'game', 'completed']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'game': forms.Select(attrs={'class': 'form-control'}),
            'completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 

class AssignGameForm(forms.Form):
    game = forms.ModelChoiceField(
        queryset=EducationalGame.objects.all(),
        label="Game",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.all(),
        label="Students",
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )               
class PerformanceAlertForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentProfile.objects.none(), label="Student")
    message = forms.CharField(widget=forms.Textarea, label="Message")

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher is not None:
            self.fields['student'].queryset = teacher.assigned_students.all()

class AutomatedEmailForm(forms.Form):
    send_performance_alerts = forms.BooleanField(
        required=False,
        initial=True,
        label="Low Performance Alerts to Teachers"
    )
    send_fee_reminders = forms.BooleanField(
        required=False,
        initial=True,
        label="Pending Fee Reminders to Parents"
    )           


class EducationalGameForm(forms.ModelForm):
    class Meta:
        model = EducationalGame
        fields = ['name', 'description', 'game_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'game_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/game'})
        }    



class NotificationSubmissionForm(forms.ModelForm):
    class Meta:
        model = NotificationSubmission
        fields = ['file']