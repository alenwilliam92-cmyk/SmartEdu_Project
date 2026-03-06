from myapp import views
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('parent_dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
              
    path('register-teacher/', views.create_teacher, name='register_teacher'),       # Enhanced URL
    path('teachers/', views.teacher_list, name='teacher_list'),                     # Teacher list
    path('edit_teacher/<int:pk>/', views.edit_teacher, name='edit_teacher'),        # Edit teacher
    path('delete_teacher/<int:pk>/', views.delete_teacher, name='delete_teacher'), # Delete teacher
    path('feedback/', views.feedback, name='feedback'),
    path('students/register/', views.register_student, name='register_student'),
    path('students/', views.student_list, name='student_list'),
    path('edit_student/<int:pk>/', views.edit_student, name='edit_student'),
    path('delete_student/<int:pk>/', views.delete_student, name='delete_student'),
    path('students/update_score/<int:pk>/', views.update_performance_score, name='update_performance_score'),
    path('teachers/assignments/', views.teacher_assignment_list, name='teacher_assignment_list'),
    path('teachers/assign/<int:pk>/', views.assign_students, name='assign_students'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('studentss/<int:pk>/', views.student_profile, name='student_profile'),
    path('monitor_students/', views.monitor_student_applications, name='monitor_student_applications'),
    
    
    path('pay-fees/', views.pay_fees, name='pay_fees'),
    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('student/<int:pk>/performance/', views.student_performance_analysis, name='student_performance_analysis'),
    path('all_students_performance/', views.all_students_performance, name='all_students_performance'),
    path('performance_analysis/', views.teacher_students_performance, name='teacher_students_performance'),
    
    path('performance_report/', views.parent_performance_report, name='parent_performance_report'),
    path('link-student/', views.link_student_to_parent, name='link_student'),
    path('play-math-quiz/', views.play_math_quiz, name='play_math_quiz'),
    path('play-word-shuffle/', views.play_word_shuffle, name='play_word_shuffle'),
    path('play-quick-add/', views.play_quick_add, name='play_quick_add'),
    path('games/', views.educational_games, name='educational_games'),

    path('assign-activity/', views.assign_activity, name='assign_activity'),
    path('personalized/', views.personalized_dashboard, name='personalized_dashboard'),
    path('progress/', views.track_progress, name='track_progress'), 
    path('assign-game/', views.assign_game, name='assign_game'),
    path('update-game-score/', views.update_game_score, name='update_game_score'),
    
    path('students_notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notifications/<int:pk>/<int:activity_id>/', views.notification_detail, name='notification_detail'),
    path('send-alert/', views.send_parent_alert, name='send_parent_alert'),
    path('parent_notifications/', views.parent_notifications, name='parent_notifications'),
    path('payments_status/', views.all_students_fee_status, name='all_students_fee_status'),   
    path('admin_trigger-low-performance-emails/', views.trigger_teacher_low_performance_emails, name='trigger_teacher_low_performance_emails'),
    path('admin_trigger-pending-fee-emails/', views.trigger_parent_pending_fee_emails, name='trigger_parent_pending_fee_emails'),
    path('admin_send-automated-emails/', views.send_automated_emails, name='send_automated_emails'),
    path('thankyou/',views.thankyou, name='thankyou'),
    path('admin_notification/',views.admin_notification,name='admin_notification'),
    path('admin_games/', views.admin_game_list, name='admin_game_list'),
    path('admin_activity/', views.admin_activity_feed, name='admin_activity_feed'),
    path("students_registration-list/", views.student_registration_list, name="student_registration_list"),
    path("students_accept/<int:student_id>/", views.accept_student, name="accept_student"),
    path("students_reject/<int:student_id>/", views.reject_student, name="reject_student"),
]