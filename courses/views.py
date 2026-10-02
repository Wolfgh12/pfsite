import json
import re
import uuid
import urllib.request
import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Course, Category, Cohort, Registration, ChatMessage, ContactInquiry


@ensure_csrf_cookie
def home_view(request):
    """
    Main landing page displaying active tracks, upcoming cohorts,
    and the executive curriculum overview.
    """
    categories = Category.objects.all()
    courses = Course.objects.filter(is_active=True).select_related('category').prefetch_related(
        'cohorts'
    )
    
    # Grab open cohorts scheduled for current/future dates
    open_cohorts = Cohort.objects.filter(
        is_open_for_enrollment=True,
        course__is_active=True
    ).select_related('course').order_by('start_date')

    context = {
        'categories': categories,
        'courses': courses,
        'open_cohorts': open_cohorts,
    }
    return render(request, 'home.html', context)


def login_view(request):
    """
    Candidate & instructor portal login view.
    """
    if request.user.is_authenticated:
        return redirect('courses:dashboard')

    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('courses:dashboard')
        else:
            error_message = "Invalid credentials. Please check your username/email and password."

    return render(request, 'login.html', {'error_message': error_message})


def signup_view(request):
    """
    Candidate & student portal registration view.
    Creates account and authenticates session automatically.
    """
    if request.user.is_authenticated:
        return redirect('courses:dashboard')

    error_message = None

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not (username and email and password):
            error_message = "Please complete all required fields."
        elif password != confirm_password:
            error_message = "Passwords do not match."
        elif len(password) < 6:
            error_message = "Password must be at least 6 characters long."
        elif User.objects.filter(username__iexact=username).exists():
            error_message = "This username is already taken. Please choose another."
        elif User.objects.filter(email__iexact=email).exists():
            error_message = "An account with this email address already exists."
        else:
            names = full_name.split(' ', 1)
            first_name = names[0] if names else ''
            last_name = names[1] if len(names) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            login(request, user)
            return redirect('courses:dashboard')

    return render(request, 'signup.html', {'error_message': error_message})


def logout_view(request):
    """
    Terminates session and redirects to home.
    """
    logout(request)
    return redirect('courses:home')


@login_required
def dashboard_view(request):
    """
    Candidate learning dashboard showing active cohort enrollments,
    status badges, access to course study materials, and direct chat thread with Mike.
    """
    registrations = Registration.objects.filter(
        email__iexact=request.user.email
    ).select_related('cohort', 'cohort__course').order_by('-id')

    chat_messages = ChatMessage.objects.filter(user=request.user).order_by('created_at')

    context = {
        'registrations': registrations,
        'chat_messages': chat_messages,
    }
    return render(request, 'dashboard.html', context)


def course_detail_view(request, slug):
    """
    Detailed curriculum view for a single program track.
    """
    course = get_object_or_404(Course, slug=slug, is_active=True)
    open_cohorts = course.cohorts.filter(is_open_for_enrollment=True).order_by('start_date')
    
    context = {
        'course': course,
        'open_cohorts': open_cohorts,
        'deliverables': course.get_deliverables_list(),
    }
    return render(request, 'courses/detail.html', context)


def all_programs_view(request):
    """
    Renders the complete catalog of all training programs, certifications,
    and scheduled cohorts with real-time search and category filtering.
    """
    categories = Category.objects.all()
    courses = Course.objects.filter(is_active=True).select_related('category').prefetch_related('cohorts')

    context = {
        'categories': categories,
        'courses': courses,
    }
    return render(request, 'allprograms.html', context)


@require_POST
def register_cohort_view(request):
    """
    Processes candidate enrollment. Supports both standard form POST
    and asynchronous JSON submissions from the PWA front-end.
    """
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.content_type == 'application/json'
    )

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload.'}, status=400)
    else:
        data = request.POST

    cohort_id = data.get('cohort_id')
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    organization = data.get('organization', '').strip()
    experience_level = data.get('experience_level', Registration.ExperienceLevel.MID)

    # Basic Validation
    if not (cohort_id and full_name and email and phone):
        error_msg = "Please provide all required fields: Name, Email, Phone, and Cohort."
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('courses:home')

    cohort = get_object_or_404(Cohort, id=cohort_id)

    if not cohort.is_open_for_enrollment:
        error_msg = f"Cohort {cohort.cohort_code} is currently closed for new enrollments."
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('courses:home')

    # Create Registration
    registration = Registration.objects.create(
        cohort=cohort,
        full_name=full_name,
        email=email,
        phone=phone,
        organization=organization,
        experience_level=experience_level,
        status=Registration.Status.PENDING,
        payment_status=Registration.PaymentStatus.UNPAID
    )

    success_msg = (
        f"Enrollment submitted successfully for {cohort.course.title} ({cohort.cohort_code}). "
        "Our academic coordinator will reach out within 24 hours with onboarding details."
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'message': success_msg,
            'registration_id': registration.id
        }, status=201)

    messages.success(request, success_msg)
    return redirect('courses:home')


def contact_mike_view(request):
    """
    Direct mailbox dispatch to Mike Awuah (nanayeezy@gmail.com).
    Handles GET page requests, full Web Inquiry Form submissions, 
    and authenticated candidate live chat messages.
    """
    if request.method == 'GET':
        return render(request, 'contact_mike.html')

    # Detect AJAX or JSON API requests
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.content_type == 'application/json'
    )

    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid payload.'}, status=400)
    else:
        payload = request.POST

    is_chat = payload.get('is_chat', False)
    message_text = payload.get('message', '').strip()

    if not message_text:
        error_msg = "Please provide a message."
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
        messages.error(request, error_msg)
        return render(request, 'contact_mike.html')

    # Channel 1: Authenticated Live Chat Message
    if is_chat:
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Sign-in required for live chat.'}, status=401)

        ChatMessage.objects.create(
            user=request.user,
            message=message_text,
            is_from_director=False
        )

        sender_name = request.user.get_full_name() or request.user.username
        sender_email = request.user.email
        email_subject = f"[Live Chat Alert][PF-ID:{request.user.id}] Message from {sender_name}"
        email_body = (
            f"--- Reply above this line to post directly to candidate's chat thread ---\n\n"
            f"Candidate Live Chat Message for Mike Awuah:\n\n"
            f"Candidate Name: {sender_name}\n"
            f"Candidate ID: #{request.user.id}\n"
            f"Username: {request.user.username}\n"
            f"Email: {sender_email}\n\n"
            f"Message:\n{message_text}\n"
        )

    # Channel 2: Direct Web Inquiry Form (Open to all visitors)
    else:
        sender_name = (payload.get('full_name') or payload.get('name', '')).strip()
        sender_email = payload.get('email', '').strip()
        subject_topic = payload.get('subject', '').strip()

        if not (sender_name and sender_email):
            error_msg = "Please provide your name and email address."
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'contact_mike.html')

        stored_message = f"[Topic: {subject_topic}]\n\n{message_text}" if subject_topic else message_text

        ContactInquiry.objects.create(
            full_name=sender_name,
            email=sender_email,
            message=stored_message
        )

        subject_prefix = f"[Project Focus Inquiry - {subject_topic}]" if subject_topic else "[Project Focus Inquiry]"
        email_subject = f"{subject_prefix} From {sender_name}"
        email_body = (
            f"Direct Web Inquiry for Director Mike Awuah:\n\n"
            f"Sender Name: {sender_name}\n"
            f"Sender Email: {sender_email}\n"
            f"Inquiry Topic: {subject_topic or 'General'}\n\n"
            f"Message:\n{message_text}\n"
        )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nanayeezy@gmail.com')
    recipient_list = ['nanayeezy@gmail.com']

    try:
        email_msg = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=from_email,
            to=recipient_list,
            reply_to=[sender_email] if sender_email else [from_email],
        )
        email_msg.send(fail_silently=False)
    except Exception as e:
        print(f"[Mail Dispatch Notice]: {e}")

    success_msg = "Your inquiry has been logged with the Directorate. Director Mike Awuah will review your transmission and respond shortly."

    if is_ajax:
        return JsonResponse({'status': 'success', 'message': success_msg})

    return render(request, 'contact_mike.html', {'success_message': success_msg})


@csrf_exempt
@require_POST
def inbound_email_webhook(request):
    """
    Inbound email webhook listener.
    Parses incoming email replies from Mike, matches the candidate token [PF-ID:X],
    strips email quote headers, and saves Mike's response directly into ChatMessage.
    """
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    else:
        payload = request.POST

    subject = (
        payload.get('Subject') or 
        payload.get('subject') or 
        payload.get('headers', {}).get('Subject', '')
    )
    
    raw_message = (
        payload.get('stripped-text') or 
        payload.get('TextBody') or 
        payload.get('text') or 
        payload.get('body-plain') or 
        payload.get('message', '')
    )

    if not raw_message:
        return JsonResponse({'status': 'ignored', 'message': 'No text body found.'}, status=200)

    token_match = re.search(r'\[PF-ID:\s*(\d+)\]', subject, re.IGNORECASE)
    if not token_match:
        token_match = re.search(r'Candidate ID:\s*#(\d+)', raw_message, re.IGNORECASE)

    if not token_match:
        return JsonResponse({'status': 'ignored', 'message': 'No candidate token found.'}, status=200)

    candidate_id = int(token_match.group(1))
    candidate = User.objects.filter(id=candidate_id).first()
    if not candidate:
        return JsonResponse({'status': 'error', 'message': 'Candidate not found.'}, status=404)

    clean_message = raw_message
    quote_delimiters = [
        r'--- Reply above this line.*',
        r'On\s+.*\s+wrote:.*',
        r'From:.*',
        r'Sent from my .*',
        r'Get Outlook for .*'
    ]
    for delimiter in quote_delimiters:
        clean_message = re.split(delimiter, clean_message, flags=re.IGNORECASE | re.DOTALL)[0]

    clean_message = clean_message.strip()
    if not clean_message:
        return JsonResponse({'status': 'ignored', 'message': 'Empty message body after cleanup.'}, status=200)

    ChatMessage.objects.create(
        user=candidate,
        message=clean_message,
        is_from_director=True
    )

    return JsonResponse({
        'status': 'success', 
        'message': f'Reply from Mike successfully logged to candidate #{candidate.id} thread.'
    }, status=200)


def mike_login_view(request):
    """
    Dedicated executive login gate for Director Mike Awuah and staff admins.
    Supports login via either Username OR Email address.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('courses:director_dashboard')

    error_message = None

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        auth_username = identifier
        if '@' in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if user_obj:
                auth_username = user_obj.username

        user = authenticate(request, username=auth_username, password=password)

        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                return redirect('courses:director_dashboard')
            else:
                error_message = "Access restricted: This account does not have Staff status enabled in Django Admin."
        else:
            error_message = "Invalid Directorate credentials. Please check your username/email and password."

    return render(request, 'mike_login.html', {'error_message': error_message})


def director_dashboard_view(request):
    """
    Executive command center for Mike Awuah:
    Aggregates registrations, inquiries, and candidate live chat threads.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect('courses:mike_login')

    registrations = Registration.objects.select_related('cohort', 'cohort__course').order_by('-created_at')
    inquiries = ContactInquiry.objects.all().order_by('-created_at')
    
    chat_candidates = User.objects.filter(chat_messages__isnull=False).distinct().order_by('-id')
    
    selected_user_id = request.GET.get('candidate_id')
    active_candidate = None
    candidate_messages = []

    if selected_user_id:
        active_candidate = User.objects.filter(id=selected_user_id).first()
    elif chat_candidates.exists():
        active_candidate = chat_candidates.first()

    if active_candidate:
        candidate_messages = ChatMessage.objects.filter(user=active_candidate).order_by('created_at')

    context = {
        'registrations': registrations,
        'inquiries': inquiries,
        'chat_candidates': chat_candidates,
        'active_candidate': active_candidate,
        'candidate_messages': candidate_messages,
    }
    return render(request, 'director_dashboard.html', context)


@require_POST
def director_reply_chat_view(request):
    """
    Enables Mike to post replies directly into the candidate's thread:
    Posts on-site and dispatches an instant email to the student.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized directorate access.'}, status=403)

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.content_type == 'application/json'
    )

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    else:
        data = request.POST

    candidate_id = data.get('candidate_id')
    reply_text = data.get('message', '').strip()

    if not (candidate_id and reply_text):
        return JsonResponse({'status': 'error', 'message': 'Candidate ID and message text are required.'}, status=400)

    candidate = get_object_or_404(User, id=candidate_id)

    # 1. Save chat message into database
    msg = ChatMessage.objects.create(
        user=candidate,
        message=reply_text,
        is_from_director=True
    )

    # 2. Forward reply to candidate's personal email
    if candidate.email:
        candidate_name = candidate.get_full_name() or candidate.first_name or candidate.username
        email_subject = "New Response from Director Mike Awuah | Project Focus"
        email_body = (
            f"Dear {candidate_name},\n\n"
            f"Director Mike Awuah has responded to your consultation inquiry:\n\n"
            f"\"{reply_text}\"\n\n"
            f"You can view your message history and continue chatting anytime from your candidate portal:\n"
            f"{request.build_absolute_uri(reverse('courses:dashboard'))}\n\n"
            f"Best regards,\n"
            f"Project Focus Directorate Office\n"
            f"Accra • London • Lagos"
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nanayeezy@gmail.com')

        try:
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=from_email,
                recipient_list=[candidate.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"[Director Email Dispatch Error]: {e}")

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'message': 'Reply dispatched to dashboard and student email.',
            'chat_id': msg.id,
            'created_at': msg.created_at.strftime('%d %b %Y, %H:%M')
        })

    messages.success(request, f"Reply dispatched to {candidate.username}.")
    return redirect(f"{reverse('courses:director_dashboard')}?candidate_id={candidate.id}")


@login_required
def initiate_paystack_payment_view(request, registration_id):
    """
    Initializes a Paystack transaction for an unpaid registration
    and redirects the candidate directly to the secure checkout portal.
    """
    registration = get_object_or_404(Registration, id=registration_id)

    if registration.email.lower() != request.user.email.lower() and not request.user.is_staff:
        messages.error(request, "Unauthorized access to this registration invoice.")
        return redirect('courses:dashboard')

    if registration.payment_status == Registration.PaymentStatus.PAID:
        messages.info(request, "Tuition for this cohort has already been settled.")
        return redirect('courses:dashboard')

    fee_subunits = int(registration.cohort.course.fee * 100)
    reference = f"PF-{registration.id}-{uuid.uuid4().hex[:10]}"
    callback_url = request.build_absolute_uri(reverse('courses:verify_payment'))

    paystack_secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')

    payload = {
        "email": registration.email,
        "amount": fee_subunits,
        "reference": reference,
        "callback_url": callback_url,
        "metadata": {
            "registration_id": registration.id,
            "cohort_code": registration.cohort.cohort_code,
            "course_title": registration.cohort.course.title,
            "student_name": registration.full_name,
        }
    }

    try:
        req = urllib.request.Request(
            'https://api.paystack.co/transaction/initialize',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {paystack_secret_key}',
                'Content-Type': 'application/json',
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))

            if result.get('status') and 'data' in result:
                authorization_url = result['data']['authorization_url']
                return redirect(authorization_url)
            else:
                messages.error(request, result.get('message', 'Unable to initialize transaction with Paystack.'))
                return redirect('courses:dashboard')

    except Exception as err:
        messages.error(request, f"Payment gateway connection error: {str(err)}")
        return redirect('courses:dashboard')


@login_required
def verify_paystack_payment_view(request):
    """
    Handles Paystack return redirect, confirms transaction validity via API,
    and updates registration records to PAID status.
    """
    reference = request.GET.get('reference') or request.GET.get('trxref')

    if not reference:
        messages.error(request, "Missing payment transaction reference.")
        return redirect('courses:dashboard')

    paystack_secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')

    try:
        verify_url = f'https://api.paystack.co/transaction/verify/{urllib.parse.quote(reference)}'
        req = urllib.request.Request(
            verify_url,
            headers={
                'Authorization': f'Bearer {paystack_secret_key}',
                'Content-Type': 'application/json',
            },
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))

            if result.get('status') and result.get('data', {}).get('status') == 'success':
                metadata = result['data'].get('metadata', {})
                registration_id = metadata.get('registration_id')

                if registration_id:
                    registration = get_object_or_404(Registration, id=registration_id)
                    registration.payment_status = Registration.PaymentStatus.PAID
                    registration.status = Registration.Status.CONFIRMED
                    registration.save()

                    messages.success(
                        request,
                        f"Payment verified successfully! Welcome to {registration.cohort.cohort_code}."
                    )
                else:
                    messages.success(request, "Payment verified, but registration reference could not be matched.")
            else:
                messages.error(request, "Payment was not completed or failed verification.")

    except Exception as err:
        messages.error(request, f"Error verifying payment: {str(err)}")

    return redirect('courses:dashboard')


@require_GET
def service_worker_view(request):
    """
    Serves the Service Worker file from the root domain scope (/)
    so it can cache and control the entire PWA application.
    """
    sw_path = settings.BASE_DIR / 'static' / 'js' / 'sw.js'
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "// Service worker file missing from static/js/sw.js"

    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


@require_GET
def offline_view(request):
    """
    Offline fallback view rendered by the PWA service worker
    when the user has no network connectivity.
    """
    return render(request, 'offline.html')