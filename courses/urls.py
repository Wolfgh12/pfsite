from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('programs/', views.all_programs_view, name='all_programs'),
    path('course/<slug:slug>/', views.course_detail_view, name='detail'),
    path('register/', views.register_cohort_view, name='register'),
    path('contact-mike/', views.contact_mike_view, name='contact_mike'),
    path('ask-a-question/', views.ask_question_view, name='ask_question'),
    path('api/cohorts/seats/', views.cohort_seats_api_view, name='cohort_seats_api'),
    path('api/inbound-email/', views.inbound_email_webhook, name='inbound_email'),
    path('director/login/', views.mike_login_view, name='mike_login'),
    path('director/', views.director_dashboard_view, name='director_dashboard'),
    path('director/chat/reply/', views.director_reply_chat_view, name='director_reply_chat'),
    path('director/ticket/answer/', views.director_answer_ticket_view, name='director_answer_ticket'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('pay/<int:registration_id>/', views.initiate_paystack_payment_view, name='pay'),
    path('payment/verify/', views.verify_paystack_payment_view, name='verify_payment'),
    path('offline/', views.offline_view, name='offline'),
]