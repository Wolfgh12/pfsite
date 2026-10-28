import os
import time
import json
import re
import uuid
import urllib.request
import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect


def handle_executive_video_upload(file_obj):
    """
    Validates and stores executive video uploads for Message of the Moment.
    Enforces a strict 15MB file cap and allows MP4, WEBM, and MOV formats.
    """
    allowed_extensions = ['.mp4', '.webm', '.mov', '.m4v']
    ext = os.path.splitext(file_obj.name)[1].lower()

    if ext not in allowed_extensions:
        return False, f"Unsupported video format '{ext}'. Please upload an MP4, WEBM, or MOV video file."

    max_size = 15 * 1024 * 1024  # 15 MB
    if file_obj.size > max_size:
        size_mb = file_obj.size / (1024 * 1024)
        return False, f"File size ({size_mb:.1f}MB) exceeds the 15MB limit. Please compress or trim the video."

    save_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
    os.makedirs(save_dir, exist_ok=True)

    timestamp = int(time.time())
    filename = f"moment_{timestamp}{ext}"
    destination_path = os.path.join(save_dir, filename)

    with open(destination_path, 'wb+') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)

    video_url = f"{settings.MEDIA_URL}videos/{filename}?v={timestamp}"
    return True, video_url
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
from .models import Course, Category, Cohort, Registration, ChatMessage, ContactInquiry, QuestionTicket, TicketMessage, SiteSnippet, CourseModule, ModuleQuestion
from .utils import parse_mcq_document


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


def about_view(request):
    """
    Institutional legacy and founder profile view for Mike Kofi Kwatia Awuah.
    """
    return render(request, 'about.html')

# Alias ensuring compatibility whether urls.py calls views.about or views.about_view
about = about_view


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
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
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
    Passes scheduled cohorts and delivery modules so frontend can display accordions.
    """
    course = get_object_or_404(
        Course.objects.prefetch_related('cohorts', 'modules'),
        slug=slug,
        is_active=True
    )
    open_cohorts = course.cohorts.filter(is_open_for_enrollment=True).order_by('start_date')
    deliverables = course.get_deliverables_list()

    # Stage unsaved specifications in preview mode if viewing this course
    if request.session.get('site_editor_preview') and request.session.get('course_editor_draft'):
        draft = request.session['course_editor_draft']
        if draft.get('course_id') == course.id:
            course.duration_weeks = draft.get('duration_weeks', course.duration_weeks)
            course.duration_unit = draft.get('duration_unit', course.duration_unit)
            course.contact_hours = draft.get('contact_hours', course.contact_hours)
            course.fee = draft.get('fee', course.fee)
            course.schedule_details = draft.get('schedule_details', course.schedule_details)
            course.tagline = draft.get('tagline', course.tagline)
            course.overview = draft.get('overview', course.overview)
            if 'is_under_construction' in draft:
                course.is_under_construction = draft['is_under_construction']
            raw_deliv = draft.get('deliverables', '')
            if raw_deliv:
                deliverables = [line.strip() for line in raw_deliv.splitlines() if line.strip()]
    
    context = {
        'course': course,
        'open_cohorts': open_cohorts,
        'deliverables': deliverables,
        'modules': course.modules.all(),
    }
    return render(request, 'courses/detail.html', context)


def course_classroom_view(request, slug):
    """
    Freemium Classroom Portal:
    Preview module(s) remain open for guest discovery.
    Subsequent modules and answer keys require candidate authentication.
    Aligned with PMBOK 8th Edition Systems Delivery, AI Integration & Value Governance.
    """
    course = get_object_or_404(
        Course.objects.prefetch_related('modules', 'cohorts'),
        slug=slug,
        category__slug='certifications',
        is_active=True
    )
    modules = list(course.modules.all())

    # Domain-specific scenario generator tailored to the exact curriculum of each module
    def get_tailored_scenarios_for_module(order, title):
        domain_contexts = {
            1: ("Foundations & Systems Architecture", "systemic boundary failure across cross-functional streams", "System Archetype Modeling"),
            2: ("Delivery Approaches & Hybrid Strategy", "misalignment between predictive stage-gates and rapid iterative release cadences", "Hybrid Value Governance Matrix"),
            3: ("Value Delivery Systems", "output volume diverging from actual realized business value and revenue indicators", "Benefits Realization Telemetry"),
            4: ("Project Environment & Enterprise Factors", "sudden regulatory policy shifts and statutory compliance overhauls", "PESTLE Environmental Impact Model"),
            5: ("Governance & Boardroom Oversight", "unauthorized executive side-channels bypassing steering committee authorization", "Steering Governance Escalation Protocol"),
            6: ("Stakeholder Engagement & Diplomacy", "key organizational influencers actively opposing core transformation milestones", "Stakeholder Power-Interest Neutralization"),
            7: ("Communications & Information Telemetry", "information filtering and delayed status distortion between site teams and the C-suite", "Radical Candor Status Architecture"),
            8: ("Knowledge Management & Tacit Capture", "critical technical know-how evaporating due to key lead developer turnover", "Tacit Knowledge Shadowing Matrix"),
            9: ("Teaming Dynamics & Psychological Safety", "inter-team friction stalling throughput during the storming-to-norming transition", "High-Performance Team Operating Agreement"),
            10: ("Leadership & Conflict Resolution", "unresolved architectural disputes between engineering leads and commercial directors", "Situational De-escalation Protocol"),
            11: ("Methodology, Systems Planning & Baselines", "planning optimism bias causing unrealistic execution dependencies", "Reference Class Forecasting Baseline"),
            12: ("Scope Management & WBS Decomposition", "unapproved functional creep inflating deliverable work packages without budget adjustments", "100% Rule WBS Dictionary Audit"),
            13: ("Quality Management & Assurance Audits", "recurring deliverable quality defects bypassing initial inspection checkpoints", "Cost of Quality (COQ) Failure Root-Cause"),
            14: ("Resource Management & Leveling", "critical specialist bottlenecks causing concurrent work package starvation", "Critical Chain Resource Leveling"),
            15: ("Financial Management & EVM Accounting", "negative cost variance and slippage indicated by EVM thresholds (CPI < 0.88, SPI < 0.90)", "Earned Value Corrective Action (CAPA) Plan"),
            16: ("Change Management & Integrated Control", "unauthorized field engineering adjustments implemented without CCB approval", "Integrated Change Control Gate Review"),
            17: ("Risk Management & Reserve Allocation", "unforeseen third-party interface threats triggering emergency contingency spend", "Expected Monetary Value (EMV) Reserve Recalibration"),
            18: ("Procurement Governance & Contracts", "vendor milestone delays accompanied by disputed progress billing claims", "FIDIC/Turnkey Liquidated Damages Audit"),
            19: ("Schedule Management & Critical Path", "total float erosion on zero-float critical path sequences threatening target delivery", "Schedule Crashing & Fast-Tracking Evaluation"),
            20: ("Project Closure & Acceptance Handover", "unresolved punch-list items and disputed liability handover hindering final sign-off", "Client Acceptance Handover & Liability Release"),
        }

        domain, risk_issue, tool = domain_contexts.get(order, (
            title,
            f"operational complexity variance regarding '{title}'",
            "PMBOK 8th Edition Systems Delivery Standard"
        ))

        scenarios = []
        for i in range(1, 21):
            q_text = (
                f"Enterprise Scenario {i:02d} ({domain}):\n"
                f"During high-stakes delivery, an emergency variance emerged involving {risk_issue}. "
                f"As Project Director, what governance mechanism and analytical framework ({tool}) must you execute "
                f"to protect delivery integrity and present a defensible trade-off to the Steering Committee?"
            )
            a_text = (
                f"Official Marking Rubric {i:02d} ({domain} Standard — 100 Marks):\n"
                f"• Immediate Containment (30M): Isolate baseline deviation boundaries; enforce formal freeze on unapproved workflows.\n"
                f"• Analytical Ground-Truth (35M): Deploy {tool} to quantify cost, schedule, and quality variances against baseline thresholds.\n"
                f"• Steering Authorization (35M): Submit a 3-tier decision paper (Absorb contingency reserve, descope non-critical work packages, or re-baseline schedule gates)."
            )
            scenarios.append({'num': i, 'q': q_text, 'a': a_text})
        return scenarios

    # Ensure all courses always present the full 20-module executive sequence
    if len(modules) < 20:
        base_list = course.get_modules_list()
        while len(base_list) < 20:
            base_list.append(f"Advanced Systems Execution Part {len(base_list) + 1}")

        existing_orders = {m.order for m in modules}

        for idx in range(1, 21):
            if idx not in existing_orders:
                title = base_list[idx - 1]
                modules.append(course.modules.model(
                    course=course,
                    order=idx,
                    title=title,
                    synopsis=f"PMBOK® 8th Edition executive delivery mechanics and systems governance framework for {title}.",
                    lecture_notes=(
                        f"PMBOK® Guide 8th Edition Strategic Outline — Module {idx:02d}: {title}\n"
                        f"• Systems Thinking & Value Delivery Networks: Aligning operational throughput with enterprise strategy.\n"
                        f"• AI-Assisted Project Telemetry: Leveraging machine learning heuristics for schedule variance and risk sensing.\n"
                        f"• Next-Gen Hybrid Governance: Harmonizing predictive compliance gates with adaptive value-stream cadences.\n"
                        f"• ESG & Sustainable Stewardship: Verifying statutory, environmental, and ethical baselines in contract execution."
                    ),
                    is_preview=(idx == 1)
                ))

        modules.sort(key=lambda m: m.order)

    # Attach interactive relational MCQs if uploaded, or fallback to tailored scenarios
    for m in modules:
        db_mcqs = list(m.mcq_questions.all().order_by('order'))
        if db_mcqs:
            m.assessment_mcqs = db_mcqs
            m.has_mcqs = True
            m.total_scenarios_count = len(db_mcqs)
        else:
            m.has_mcqs = False
            scenarios = get_tailored_scenarios_for_module(m.order, m.title)
            m.assessment_pages = [
                {'page_num': page_idx + 1, 'items': scenarios[page_idx * 4 : (page_idx + 1) * 4]}
                for page_idx in range(5)
            ]
            m.total_scenarios_count = len(scenarios)

    # Switch active module via ?module=2 or default to module 1
    selected_order = request.GET.get('module')
    active_module = None
    if selected_order and selected_order.isdigit():
        active_module = next((m for m in modules if m.order == int(selected_order)), None)

    if not active_module and modules:
        active_module = modules[0]

    # Stage unsaved module draft in preview mode
    is_preview_mode = bool(request.session.get('site_editor_preview'))
    if is_preview_mode and request.session.get('module_editor_draft'):
        m_draft = request.session['module_editor_draft']
        if active_module and m_draft.get('course_id') == course.id and m_draft.get('order') == active_module.order:
            active_module.title = m_draft.get('title', active_module.title)
            active_module.synopsis = m_draft.get('synopsis', active_module.synopsis)
            active_module.slide_deck_url = m_draft.get('slide_deck_url', active_module.slide_deck_url)
            active_module.lecture_notes = m_draft.get('lecture_notes', active_module.lecture_notes)
            active_module.task_question = m_draft.get('task_question', active_module.task_question)
            active_module.task_solution = m_draft.get('task_solution', active_module.task_solution)

    # Scenario A: Gating logic - temporarily unlock module for previewing director
    is_locked = False
    if not (request.user.is_authenticated or is_preview_mode) and active_module and not active_module.is_preview:
        is_locked = True
    elif is_preview_mode and active_module:
        active_module.is_preview = True
        is_locked = False

    # Safely resolve slide deck source on all modules without raising FieldFile ValueError
    for m in modules:
        try:
            m.deck_src = m.slide_deck_file.url if bool(m.slide_deck_file) else (m.slide_deck_url or '')
        except (ValueError, AttributeError):
            m.deck_src = m.slide_deck_url or ''

    context = {
        'course': course,
        'modules': modules,
        'active_module': active_module,
        'is_locked': is_locked,
        'is_preview_mode': is_preview_mode,
    }
    return render(request, 'courses/classroom.html', context)


def all_programs_view(request):
    """
    Renders exclusively the Corporate Project Management Training catalog,
    organized across three execution tiers: Fundamentals, Intermediate, and Advanced.
    """
    courses = Course.objects.filter(
        is_active=True,
        category__slug='corporate-training'
    ).select_related('category').prefetch_related('cohorts', 'modules')

    context = {
        'courses': courses,
        'selected_tier': request.GET.get('tier', 'fundamentals').strip().lower(),
        'fundamentals_count': courses.filter(level='fundamentals').count(),
        'intermediate_count': courses.filter(level='intermediate').count(),
        'advanced_count': courses.filter(level='advanced').count(),
    }
    return render(request, 'allprograms.html', context)


def certifications_view(request):
    """
    Renders dedicated page for PM Certifications (CAPM, PMP, RMP, SMP).
    """
    courses = Course.objects.filter(
        is_active=True,
        category__slug='certifications'
    ).select_related('category').prefetch_related('cohorts')

    return render(request, 'certifications.html', {'courses': courses})


def consulting_view(request):
    """
    Renders dedicated page for Project Management Consulting & Advisory.
    """
    services = Course.objects.filter(
        is_active=True,
        category__slug='consulting'
    ).select_related('category')

    return render(request, 'consulting.html', {'services': services})


def book_session_view(request):
    """
    Executive corporate consultation and session booking with Director Mike Awuah.
    Saves to ContactInquiry (tagged as Corporate Training) and dispatches alert email.
    """
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        job_title = request.POST.get('job_title', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        organization = request.POST.get('organization', '').strip()
        industry = request.POST.get('industry', '').strip()
        subject = request.POST.get('subject', '').strip()
        cohort_size = request.POST.get('cohort_size', '').strip()
        delivery_mode = request.POST.get('delivery_mode', '').strip()
        objectives = request.POST.get('message', '').strip()

        formatted_message = (
            f"\n"
            f"Target Training Track: {subject}\n"
            f"Executive Role: {job_title}\n"
            f"Organization: {organization} (Sector: {industry})\n"
            f"Phone / WhatsApp: {phone}\n"
            f"Cohort Scale: {cohort_size}\n"
            f"Delivery Format: {delivery_mode}\n\n"
            f"Key Objectives & Operational Context:\n{objectives}"
        )

        ContactInquiry.objects.create(
            full_name=f"{full_name} ({organization})",
            email=email,
            message=formatted_message
        )

        email_subject = f"[Corporate Training Booking] {subject} - {organization}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nanayeezy@gmail.com')
        recipient_list = ['mike.awuah@projectfocus.com', 'nanayeezy@gmail.com']

        try:
            email_msg = EmailMessage(
                subject=email_subject,
                body=formatted_message,
                from_email=from_email,
                to=recipient_list,
                reply_to=[email] if email else [from_email],
            )
            email_msg.send(fail_silently=True)
        except Exception as e:
            print(f"[Corporate Booking Mail Error]: {e}")

        messages.success(
            request,
            f"Thank you, {full_name}. Your corporate session request for {organization} has been transmitted directly to Director Mike Awuah. An executive response will be issued within 24 business hours."
        )
        return redirect('courses:book_session')

    return render(request, 'courses/book_session.html')


@require_POST
def register_cohort_view(request):
    """
    Processes candidate enrollment. Supports both standard form POST
    and asynchronous JSON submissions from the PWA front-end.
    Validates live cohort seat capacity and intake availability.
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

    # Validate Capacity & Intake Status
    if not cohort.is_available:
        if cohort.is_full:
            error_msg = (
                f"Cohort {cohort.cohort_code} has reached its maximum capacity of "
                f"{cohort.max_seats} candidates and is closed for this intake. Please choose an upcoming cohort."
            )
        else:
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

    # Check if this registration filled the final seat
    remaining = cohort.seats_remaining
    seat_status_note = f" ({remaining} seats remaining)" if remaining > 0 else " (Cohort is now fully booked)"

    success_msg = (
        f"Enrollment confirmed for {cohort.course.title} [{cohort.cohort_code}]{seat_status_note}. "
        "Our academic coordinator will reach out within 24 hours with onboarding details."
    )

    if is_ajax:
        return JsonResponse({
            'status': 'success',
            'message': success_msg,
            'registration_id': registration.id,
            'seats_remaining': remaining
        }, status=201)

    messages.success(request, success_msg)
    return redirect('courses:home')


@require_GET
def cohort_seats_api_view(request):
    """
    Lightweight background polling endpoint returning real-time seat counts,
    intake availability, and capacity caps for active cohorts.
    """
    cohorts = Cohort.objects.filter(course__is_active=True).select_related('course')
    cohort_data = {}
    for c in cohorts:
        cohort_data[c.id] = {
            'seats_remaining': c.seats_remaining,
            'max_seats': c.max_seats,
            'registered_count': c.registered_count,
            'is_full': c.is_full,
            'is_available': c.is_available,
        }
    return JsonResponse({'status': 'success', 'cohorts': cohort_data})


def contact_mike_view(request):
    """
    Direct mailbox dispatch to awuah (nanayeezy@gmail.com).
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
            f"Candidate Live Chat Message for awuah:\n\n"
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
            f"Direct Web Inquiry for Director awuah:\n\n"
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

    success_msg = "Your inquiry has been logged with the Directorate. Director awuah will review your transmission and respond shortly."

    if is_ajax:
        return JsonResponse({'status': 'success', 'message': success_msg})

    return render(request, 'contact_mike.html', {'success_message': success_msg})


def ask_question_view(request):
    """
    Dedicated desk for submitting questions, continuing threaded conversations,
    and reviewing director responses without requiring user accounts.
    """
    courses = Course.objects.filter(is_active=True).order_by('title')
    lookup_ticket = None
    lookup_error = None
    new_ticket = None

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.content_type == 'application/json'
    )

    # 1. Handling Ticket Code Lookup (GET query param or POST action='lookup')
    query_code = request.GET.get('ticket_number', '').strip().upper()
    if query_code:
        lookup_ticket = QuestionTicket.objects.filter(
            ticket_number__iexact=query_code
        ).select_related('course').prefetch_related('messages').first()
        if not lookup_ticket:
            lookup_error = f"No inquiry found for tracking reference '{query_code}'. Please check the code and try again."

    if request.method == 'POST':
        action = request.POST.get('action', 'submit')

        # Action A: Lookup from search form
        if action == 'lookup':
            ticket_code = request.POST.get('ticket_number', '').strip().upper()
            lookup_ticket = QuestionTicket.objects.filter(
                ticket_number__iexact=ticket_code
            ).select_related('course').prefetch_related('messages').first()

            if not lookup_ticket:
                lookup_error = f"No inquiry found for tracking reference '{ticket_code}'."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': lookup_error}, status=404)
            else:
                if is_ajax:
                    return JsonResponse({
                        'status': 'success',
                        'ticket_number': lookup_ticket.ticket_number,
                        'full_name': lookup_ticket.full_name,
                        'subject': lookup_ticket.subject or 'General Inquiry',
                        'course': lookup_ticket.course.title if lookup_ticket.course else 'General',
                        'question': lookup_ticket.question,
                        'answer': lookup_ticket.answer,
                        'is_answered': bool(lookup_ticket.answer),
                        'status_display': lookup_ticket.get_status_display(),
                        'created_at': lookup_ticket.created_at.strftime('%d %b %Y, %H:%M'),
                        'answered_at': lookup_ticket.answered_at.strftime('%d %b %Y, %H:%M') if lookup_ticket.answered_at else None,
                    })

        # Action B: Submitting a brand-new inquiry
        elif action == 'submit':
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            course_id = request.POST.get('course_id')
            subject = request.POST.get('subject', '').strip()
            question_text = request.POST.get('question', '').strip()

            if not (full_name and email and question_text):
                error_msg = "Please provide your full name, email address, and question."
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
                messages.error(request, error_msg)
            else:
                associated_course = Course.objects.filter(id=course_id).first() if course_id else None

                new_ticket = QuestionTicket.objects.create(
                    full_name=full_name,
                    email=email,
                    course=associated_course,
                    subject=subject,
                    question=question_text
                )

                # Initialize conversation thread
                TicketMessage.objects.create(
                    ticket=new_ticket,
                    sender_type=TicketMessage.SenderType.VISITOR,
                    sender_name=full_name,
                    message=question_text
                )

                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nanayeezy@gmail.com')

                # Deep link with next redirect for Director Mike
                target_dashboard = f"{reverse('courses:director_dashboard')}?tab=tickets&ticket_id={new_ticket.id}"
                mike_deep_link = request.build_absolute_uri(
                    f"{reverse('courses:mike_login')}?next={urllib.parse.quote(target_dashboard)}"
                )

                mike_alert_body = (
                    f"New Visitor Inquiry Received:\n\n"
                    f"Ticket Code: {new_ticket.ticket_number}\n"
                    f"Sender: {full_name} ({email})\n"
                    f"Subject: {subject or 'General Inquiry'}\n"
                    f"Program: {associated_course.title if associated_course else 'General'}\n\n"
                    f"Question:\n{question_text}\n\n"
                    f"--- RESPOND DIRECTLY IN COMMAND CENTER ---\n"
                    f"Click below to login and reply directly:\n"
                    f"{mike_deep_link}\n"
                )
                try:
                    send_mail(
                        subject=f"[New Inquiry Alert][{new_ticket.ticket_number}] Question from {full_name}",
                        message=mike_alert_body,
                        from_email=from_email,
                        recipient_list=['nanayeezy@gmail.com'],
                        fail_silently=True
                    )
                except Exception as e:
                    print(f"[Mike Inquiry Alert Error]: {e}")

                # Visitor confirmation email with tracking link
                lookup_url = request.build_absolute_uri(
                    f"{reverse('courses:ask_question')}?ticket_number={new_ticket.ticket_number}"
                )
                visitor_body = (
                    f"Dear {full_name},\n\n"
                    f"Thank you for contacting Project Focus. Your inquiry has been routed to Director awuah.\n\n"
                    f"Your Tracking Code: {new_ticket.ticket_number}\n\n"
                    f"Track the status and read Director Mike's response at any time here:\n"
                    f"{lookup_url}\n\n"
                    f"Subject: {subject or 'General Question'}\n"
                    f"Question:\n{question_text}\n\n"
                    f"Best regards,\n"
                    f"Project Focus Directorate Office"
                )
                try:
                    send_mail(
                        subject=f"[Project Focus] Inquiry Ticket Received ({new_ticket.ticket_number})",
                        message=visitor_body,
                        from_email=from_email,
                        recipient_list=[email],
                        fail_silently=True
                    )
                except Exception as e:
                    print(f"[Visitor Receipt Error]: {e}")

                success_msg = f"Your inquiry has been logged under ticket reference {new_ticket.ticket_number}."
                if is_ajax:
                    return JsonResponse({
                        'status': 'success',
                        'message': success_msg,
                        'ticket_number': new_ticket.ticket_number
                    }, status=201)
                messages.success(request, success_msg)

        # Action C: Visitor follow-up message on existing ticket
        elif action == 'reply':
            ticket_code = request.POST.get('ticket_number', '').strip().upper()
            reply_text = request.POST.get('reply_message', '').strip()

            target_ticket = QuestionTicket.objects.filter(ticket_number__iexact=ticket_code).first()

            if not (target_ticket and reply_text):
                messages.error(request, "Ticket and reply content are required.")
            else:
                TicketMessage.objects.create(
                    ticket=target_ticket,
                    sender_type=TicketMessage.SenderType.VISITOR,
                    sender_name=target_ticket.full_name,
                    message=reply_text
                )
                target_ticket.status = QuestionTicket.Status.PENDING
                target_ticket.save(update_fields=['status'])

                # Dispatch follow-up alert email to Mike with deep link
                target_dashboard = f"{reverse('courses:director_dashboard')}?tab=tickets&ticket_id={target_ticket.id}"
                mike_deep_link = request.build_absolute_uri(
                    f"{reverse('courses:mike_login')}?next={urllib.parse.quote(target_dashboard)}"
                )
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nanayeezy@gmail.com')
                mike_alert_body = (
                    f"Follow-Up Message on Ticket {target_ticket.ticket_number}:\n\n"
                    f"Sender: {target_ticket.full_name} ({target_ticket.email})\n\n"
                    f"Follow-Up Message:\n{reply_text}\n\n"
                    f"--- RESPOND IN COMMAND CENTER ---\n"
                    f"Click below to login and reply:\n"
                    f"{mike_deep_link}\n"
                )
                try:
                    send_mail(
                        subject=f"[Follow-Up Alert][{target_ticket.ticket_number}] Message from {target_ticket.full_name}",
                        message=mike_alert_body,
                        from_email=from_email,
                        recipient_list=['nanayeezy@gmail.com'],
                        fail_silently=True
                    )
                except Exception as e:
                    print(f"[Mike Follow-up Alert Error]: {e}")

                messages.success(request, "Your follow-up has been transmitted to Director awuah.")
                return redirect(f"{reverse('courses:ask_question')}?ticket_number={target_ticket.ticket_number}")

    context = {
        'courses': courses,
        'lookup_ticket': lookup_ticket,
        'lookup_error': lookup_error,
        'new_ticket': new_ticket,
    }
    return render(request, 'ask_question.html', context)


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
    Dedicated executive login gate for Director awuah and staff admins.
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
    Executive command center for awuah:
    Aggregates registrations, inquiries, question tickets with conversation threads,
    and candidate live chat threads. Supports inbox deep-linking.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect('courses:mike_login')

    registrations = Registration.objects.select_related('cohort', 'cohort__course').order_by('-created_at')
    inquiries = ContactInquiry.objects.all().order_by('-created_at')
    question_tickets = QuestionTicket.objects.select_related('course').prefetch_related('messages').order_by('-created_at')
    
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

    # Deep-link support from email alerts
    target_ticket_id = request.GET.get('ticket_id')
    active_tab = request.GET.get('tab')
    if target_ticket_id and not active_tab:
        active_tab = 'tickets'
    elif not active_tab:
        active_tab = 'chatdesk'

    context = {
        'registrations': registrations,
        'inquiries': inquiries,
        'question_tickets': question_tickets,
        'chat_candidates': chat_candidates,
        'active_candidate': active_candidate,
        'candidate_messages': candidate_messages,
        'active_tab': active_tab,
        'target_ticket_id': target_ticket_id,
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
        email_subject = "New Response from Director awuah | Project Focus"
        email_body = (
            f"Dear {candidate_name},\n\n"
            f"Director awuah has responded to your consultation inquiry:\n\n"
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


@require_POST
def director_answer_ticket_view(request):
    """
    Allows Director awuah to answer candidate question tickets directly.
    Appends the message to the conversation thread, updates the ticket,
    and automatically dispatches an email alerting the inquirer with a direct reply link.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized directorate access.'}, status=403)

    ticket_id = request.POST.get('ticket_id')
    answer_text = request.POST.get('answer', '').strip()

    if not (ticket_id and answer_text):
        messages.error(request, "Ticket ID and answer content are required.")
        return redirect(f"{reverse('courses:director_dashboard')}?tab=tickets")

    ticket = get_object_or_404(QuestionTicket, id=ticket_id)

    # 1. Append Director message to conversation thread
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.DIRECTOR,
        sender_name="Director awuah",
        message=answer_text
    )

    # 2. Update parent ticket status & latest answer
    ticket.answer = answer_text
    ticket.status = QuestionTicket.Status.ANSWERED
    ticket.save()

    # 3. Forward answer to inquirer's email with direct link
    lookup_url = request.build_absolute_uri(
        f"{reverse('courses:ask_question')}?ticket_number={ticket.ticket_number}"
    )
    email_body = (
        f"Dear {ticket.full_name},\n\n"
        f"Director awuah has responded to your inquiry (Ticket: {ticket.ticket_number}):\n\n"
        f"\"{answer_text}\"\n\n"
        f"--- VIEW THREAD & REPLY DIRECTLY ---\n"
        f"You can view the full conversation and reply back to Director Mike using this link:\n"
        f"{lookup_url}\n\n"
        f"Best regards,\n"
        f"Project Focus Directorate Office"
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nanayeezy@gmail.com')

    try:
        send_mail(
            subject=f"[Project Focus] Response from Director awuah ({ticket.ticket_number})",
            message=email_body,
            from_email=from_email,
            recipient_list=[ticket.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"[Ticket Answer Dispatch Error]: {e}")

    messages.success(request, f"Response dispatched to candidate for ticket {ticket.ticket_number}.")
    return redirect(f"{reverse('courses:director_dashboard')}?tab=tickets&ticket_id={ticket.id}")


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
                    registration.status = Registration.Status.ADMITTED
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


def director_site_editor_view(request):
    """
    Dedicated toddler-proof website text editor for Director Mike Awuah.
    Restricted strictly to authenticated staff/director accounts.
    Allows changing copy across all 5 site pages, course specifications/durations,
    and classroom modules with preview-first session staging.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect('courses:mike_login')

    # Seed master default snippets on first load if missing
    DEFAULT_SNIPPETS = [
        # 1. HOMEPAGE
        {'page': 'home', 'key': 'home_top_pill_title', 'label': 'Top Video Status Pill Title', 'location_hint': 'Hero: Above main headline (left text)', 'default_value': 'Message of the Moment', 'is_multiline': False},
        {'page': 'home', 'key': 'home_top_pill_cta', 'label': 'Top Video Status Pill Action Notice', 'location_hint': 'Hero: Above main headline (colored badge on right)', 'default_value': '(Click to watch)', 'is_multiline': False},
        {'page': 'home', 'key': 'home_hero_headline_1', 'label': 'Main Headline Prefix (White)', 'location_hint': 'Hero: First word / white greeting', 'default_value': 'Welcome:', 'is_multiline': False},
        {'page': 'home', 'key': 'home_hero_headline_2', 'label': 'Main Headline Body (Glowing Gradient)', 'location_hint': 'Hero: Main headline text with blue-cyan gradient', 'default_value': 'This is a Premier Destination for Advanced Project Management Capacity Building.', 'is_multiline': False},
        {'page': 'home', 'key': 'home_manifesto_quote', 'label': 'Executive Manifesto Quote', 'location_hint': 'Hero: Italicized quote block under headline', 'default_value': 'Here we dream up, dive in, and cross the finish line with you on your projects!', 'is_multiline': False},
        {'page': 'home', 'key': 'home_hero_narrative', 'label': 'Homepage Main Narrative', 'location_hint': 'Hero: Main paragraph under manifesto banner', 'default_value': 'Project Focus is a vibrant capacity-building powerhouse, launched to bridge the gap between academic management theories and the high-stakes world of enterprise projects, capital infrastructure, public-private partnerships, and project governance through professional training, certification, and consulting!', 'is_multiline': True},
        {'page': 'home', 'key': 'home_pillar_1_title', 'label': 'Practice Area 1 Title', 'location_hint': 'Practice Areas: First card heading', 'default_value': 'Corporate Project Management Training', 'is_multiline': False},
        {'page': 'home', 'key': 'home_pillar_1_desc', 'label': 'Practice Area 1 Description', 'location_hint': 'Practice Areas: First card subtitle', 'default_value': 'Bespoke corporate capacity development, delivery simulations, and team alignment across three execution tiers:', 'is_multiline': True},
        {'page': 'home', 'key': 'home_pillar_2_title', 'label': 'Practice Area 2 Title', 'location_hint': 'Practice Areas: Second card heading', 'default_value': 'Project Management Certification', 'is_multiline': False},
        {'page': 'home', 'key': 'home_pillar_2_desc', 'label': 'Practice Area 2 Description', 'location_hint': 'Practice Areas: Second card subtitle', 'default_value': 'PMP® Exam Mastery, CAPM®, PMI-RMP®, and PMI-SP® credential programs aligned with global standards.', 'is_multiline': True},
        {'page': 'home', 'key': 'home_pillar_3_title', 'label': 'Practice Area 3 Title', 'location_hint': 'Practice Areas: Third card heading', 'default_value': 'Project Management Consulting', 'is_multiline': False},
        {'page': 'home', 'key': 'home_pillar_3_desc', 'label': 'Practice Area 3 Description', 'location_hint': 'Practice Areas: Third card subtitle', 'default_value': 'PMP® Exam Mastery, CAPM®, PMI-RMP®, and PMI-SP® credential programs aligned with global standards.', 'is_multiline': True},
        {'page': 'home', 'key': 'home_video_file', 'label': 'Message of the Moment Video Asset URL', 'location_hint': 'Hero Cinema Modal: Video stream source', 'default_value': '/media/MA.mp4', 'is_multiline': False},
        {'page': 'home', 'key': 'home_video_badge_tag', 'label': 'Video Overlay Tag Badge', 'location_hint': 'Hero Cinema Modal: Top-left glowing pill tag', 'default_value': 'TRANSMISSION 01', 'is_multiline': False},
        {'page': 'home', 'key': 'home_video_badge_label', 'label': 'Video Overlay Subtitle', 'location_hint': 'Hero Cinema Modal: Top-left subtitle next to tag', 'default_value': 'Directorate Keynote', 'is_multiline': False},
        {'page': 'home', 'key': 'home_video_title', 'label': 'Video Cinema Modal Headline', 'location_hint': 'Hero Cinema Modal: Title strip below video player', 'default_value': 'Mike on Project Focus', 'is_multiline': False},
        {'page': 'home', 'key': 'home_video_speaker', 'label': 'Video Speaker Tag', 'location_hint': 'Video Section: Pill next to video heading', 'default_value': 'Featured Speaker: Michael Awuah', 'is_multiline': False},
        {'page': 'home', 'key': 'home_video_standby_headline', 'label': 'Video Standby Screen Headline', 'location_hint': 'Video Section: Inside cinema frame', 'default_value': 'video under renovation/production', 'is_multiline': False},
        {'page': 'home', 'key': 'home_video_standby_desc', 'label': 'Video Standby Screen Description', 'location_hint': 'Video Section: Inside cinema frame subtitle', 'default_value': 'This keynote masterclass is currently undergoing editorial enhancements and curriculum alignment. The updated stream will be released shortly.', 'is_multiline': True},

        # 2. ABOUT US
        {'page': 'about', 'key': 'about_hero_badge', 'label': 'Top Genesis Badge', 'location_hint': 'Hero: Pill badge above main heading', 'default_value': 'Established in 2001 • Over Two Decades of Authority', 'is_multiline': False},
        {'page': 'about', 'key': 'about_hero_headline_1', 'label': 'About Page Headline (First Line)', 'location_hint': 'Hero: First line of large heading', 'default_value': 'Founded in 2001 by Mike Kofi Kwatia Awuah.', 'is_multiline': False},
        {'page': 'about', 'key': 'about_hero_headline_2', 'label': 'About Page Headline (Second Line)', 'location_hint': 'Hero: Glowing second line', 'default_value': 'Built into a global powerhouse.', 'is_multiline': False},
        {'page': 'about', 'key': 'about_creed_quote', 'label': 'Executive Creed Quote', 'location_hint': 'Hero: Italicized quote', 'default_value': 'Here we think, live, and perform project management.', 'is_multiline': False},
        {'page': 'about', 'key': 'about_creed_author', 'label': 'Executive Creed Subtitle', 'location_hint': 'Hero: Text under italicized quote', 'default_value': 'Founder & Executive Director Mike Kofi Kwatia Awuah', 'is_multiline': False},
        {'page': 'about', 'key': 'about_hero_narrative', 'label': 'Genesis Overview Narrative', 'location_hint': 'Hero: Main introductory paragraph', 'default_value': 'In 2001, Mike Kofi Kwatia Awuah established Project Focus to reject theoretical abstraction and instill battlefield-tested execution control into capital programs. Over twenty-five years of leadership have transformed the institute into an international powerhouse for engineering directors, state enterprises, and infrastructure PMOs worldwide.', 'is_multiline': True},
        {'page': 'about', 'key': 'about_profile_name', 'label': 'Director Name', 'location_hint': 'Founder Profile: Card caption name', 'default_value': 'Mike Kofi Kwatia Awuah', 'is_multiline': False},
        {'page': 'about', 'key': 'about_profile_role', 'label': 'Director Title', 'location_hint': 'Founder Profile: Card caption subtitle', 'default_value': 'Founder & Executive Director', 'is_multiline': False},
        {'page': 'about', 'key': 'about_profile_headline', 'label': 'Directorate Philosophy Heading', 'location_hint': 'Founder Profile: Section main title', 'default_value': 'Turning project delivery from a gamble into an exacting science.', 'is_multiline': False},
        {'page': 'about', 'key': 'about_profile_p1', 'label': 'Founder Bio: Paragraph 1', 'location_hint': 'Founder Profile: Story paragraph 1', 'default_value': 'When Mike Kofi Kwatia Awuah founded Project Focus in 2001, high-value infrastructure projects across public and private sectors routinely fell victim to the same systemic failures: ballooning budgets, missed deadlines, and unmanaged contractual disputes.', 'is_multiline': True},
        {'page': 'about', 'key': 'about_profile_p2', 'label': 'Founder Bio: Paragraph 2', 'location_hint': 'Founder Profile: Story paragraph 2', 'default_value': 'Director Mike recognized that the industry was suffocating under academic models that failed the moment dirt met the ground. He established Project Focus on a singular premise: project management must be practiced as a live discipline of risk defense, schedule baseline control, and ruthless contractual governance.', 'is_multiline': True},
        {'page': 'about', 'key': 'about_profile_p3', 'label': 'Founder Bio: Paragraph 3', 'location_hint': 'Founder Profile: Story paragraph 3', 'default_value': 'Today, what started as an intensive elite workshop has expanded into an international powerhouse. Project Focus advises government ministries, multinationals, engineering joint ventures, and capital developers, maintaining the standard that Director Mike set twenty-five years ago.', 'is_multiline': True},
        {'page': 'about', 'key': 'about_mandate_subtitle', 'label': 'Institutional Charter Subtitle', 'location_hint': 'Mandate Section: Introduction text', 'default_value': 'Twenty-five years of unrelenting discipline, distilled into our permanent direction and present execution standard.', 'is_multiline': True},
        {'page': 'about', 'key': 'about_vision_title', 'label': 'Vision Card Heading', 'location_hint': 'Mandate Section: Card 1 title', 'default_value': 'Institutional Preeminence', 'is_multiline': False},
        {'page': 'about', 'key': 'about_vision_desc', 'label': 'Vision Card Description', 'location_hint': 'Mandate Section: Card 1 description', 'default_value': 'To stand as the foremost global authority in capital projects, engineering governance, and contract administration—eradicating systemic project failures through unyielding execution discipline and baseline integrity.', 'is_multiline': True},
        {'page': 'about', 'key': 'about_mission_title', 'label': 'Mission Card Heading', 'location_hint': 'Mandate Section: Card 2 title', 'default_value': 'Bridging Theory & Delivery', 'is_multiline': False},
        {'page': 'about', 'key': 'about_mission_desc', 'label': 'Mission Card Description', 'location_hint': 'Mandate Section: Card 2 description', 'default_value': 'To equip practitioners, ministries, and enterprise institutions with battlefield-tested PMO frameworks, FIDIC contract administration mastery, and quantitative cost controls that actively defend high-stakes investments.', 'is_multiline': True},
        {'page': 'about', 'key': 'about_today_title', 'label': 'Today Card Heading', 'location_hint': 'Mandate Section: Card 3 title', 'default_value': 'The Global Powerhouse', 'is_multiline': False},
        {'page': 'about', 'key': 'about_today_desc', 'label': 'Today Card Description', 'location_hint': 'Mandate Section: Card 3 description', 'default_value': 'A premier international institution recognized for executive PMP® mastery, FIDIC dispute governance, and independent capital project diagnostics, operating under Director Mike Awuah\'s direct guidance.', 'is_multiline': True},

        # 3. CORPORATE TRAINING (allprograms.html)
        {'page': 'corporate', 'key': 'corp_header_badge', 'label': 'Catalog Status Badge', 'location_hint': 'Header: Top pill tag', 'default_value': 'Corporate Practice Directory', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_header_title', 'label': 'Corporate Catalog Title', 'location_hint': 'Header: Main page heading', 'default_value': 'Corporate Project Management Training', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_header_desc', 'label': 'Corporate Catalog Subtitle', 'location_hint': 'Header: Overview under main title', 'default_value': 'Practical in-house capacity development, real-world simulations, and execution frameworks tailored to align corporate teams with global delivery standards.', 'is_multiline': True},
        {'page': 'corporate', 'key': 'corp_step_1_tag', 'label': 'Step 01 Category Tag', 'location_hint': 'Roadmap Step 01: Cyan category badge', 'default_value': 'Context-Specific Problem Diagnosis', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_1_title', 'label': 'Step 01 Heading', 'location_hint': 'Roadmap Step 01: Main title', 'default_value': 'Solving Real-World Problems, Not Ticking Boxes', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_1_desc', 'label': 'Step 01 Description', 'location_hint': 'Roadmap Step 01: Story paragraph', 'default_value': "With these corporate programmes, we aren't just here to tick boxes! We're all about solving real-world problems for your company. We dive right in to reinforce knowledge foundations, fill those skill gaps, and tackle attitudinal hurdles. Since knowledge, attitude, and skill gaps are totally context-specific, we don't do “one-size-fits-all” wholesale programmes. We believe in truly understanding every situation to deliver the perfect intervention.", 'is_multiline': True},
        {'page': 'corporate', 'key': 'corp_step_2_tag', 'label': 'Step 02 Category Tag', 'location_hint': 'Roadmap Step 02: Electric category badge', 'default_value': 'Pedagogical Dynamics & Retention', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_2_title', 'label': 'Step 02 Heading', 'location_hint': 'Roadmap Step 02: Main title', 'default_value': 'Proven Adult Learning Techniques', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_2_desc', 'label': 'Step 02 Description', 'location_hint': 'Roadmap Step 02: Story paragraph', 'default_value': 'Each course taps into a range of proven adult learning techniques to ensure you truly grasp, understand, and remember everything presented! We’ll power up each topic with stimulating presentations, mixed with lively, interactive discussions among participants and led by the trainer.', 'is_multiline': True},
        {'page': 'corporate', 'key': 'corp_step_3_tag', 'label': 'Step 03 Category Tag', 'location_hint': 'Roadmap Step 03: Emerald category badge', 'default_value': 'Applied Simulations & Field Sandbox', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_3_title', 'label': 'Step 03 Heading', 'location_hint': 'Roadmap Step 03: Main title', 'default_value': 'Safe, Interactive Learning Environment', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_3_desc', 'label': 'Step 03 Description', 'location_hint': 'Roadmap Step 03: Story paragraph', 'default_value': 'We will achieve this through a mix of interactive exercises, role plays, individual assignments, and short theory-based lectures to help participants practice their newly learned skills in a safe learning environment. We also use fun exercises, short video presentations, and small-group work, providing feedback along the way to make learning a breeze!', 'is_multiline': True},
        {'page': 'corporate', 'key': 'corp_step_4_tag', 'label': 'Step 04 Category Tag', 'location_hint': 'Roadmap Step 04: Teal category badge', 'default_value': 'Custom Corporate Event Co-Creation', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_4_title', 'label': 'Step 04 Heading', 'location_hint': 'Roadmap Step 04: Main title', 'default_value': 'Tailored Directly to Your Specific Needs', 'is_multiline': False},
        {'page': 'corporate', 'key': 'corp_step_4_desc', 'label': 'Step 04 Description', 'location_hint': 'Roadmap Step 04: Story paragraph', 'default_value': "Give us a shout about whatever's on your mind! We’ll team up with you to craft an event that's a perfect match for all your specific needs.", 'is_multiline': True},

        # 4. CERTIFICATIONS
        {'page': 'certifications', 'key': 'cert_header_badge', 'label': 'Header Credential Badge', 'location_hint': 'Header: Top pill tag', 'default_value': 'Global Credential Preparation • PMI® REP Aligned', 'is_multiline': False},
        {'page': 'certifications', 'key': 'cert_header_title', 'label': 'Certifications Page Title', 'location_hint': 'Header: Main page heading', 'default_value': 'Project Management Certification', 'is_multiline': False},
        {'page': 'certifications', 'key': 'cert_header_desc', 'label': 'Certifications Introduction', 'location_hint': 'Header: Overview narrative under title', 'default_value': 'Intensive examination prep and competency-building tracks designed for international credentialing. Master the standard frameworks, pass your exam on the first attempt, and advance your executive standing.', 'is_multiline': True},

        # 5. CONSULTING & ADVISORY
        {'page': 'consulting', 'key': 'consulting_header_badge', 'label': 'Header Advisory Badge', 'location_hint': 'Header: Top pill tag', 'default_value': 'Directorate Advisory Desk • Capital Infrastructure & Governance', 'is_multiline': False},
        {'page': 'consulting', 'key': 'consulting_header_title', 'label': 'Consulting Page Title', 'location_hint': 'Header: Main page heading', 'default_value': 'Project Management Consulting', 'is_multiline': False},
        {'page': 'consulting', 'key': 'consulting_header_desc', 'label': 'Consulting Introduction', 'location_hint': 'Header: Overview narrative under title', 'default_value': 'Direct executive advisory led by Director awuah. We partner with public ministries, international EPC contractors, and enterprise PMOs to diagnose schedule slippages, resolve contractor claims, and institute FIDIC governance.', 'is_multiline': True},
        {'page': 'consulting', 'key': 'consulting_area_1_title', 'label': 'Advisory Area 1 Title', 'location_hint': 'Practices: Card 01 title', 'default_value': 'Project Governance Assistance', 'is_multiline': False},
        {'page': 'consulting', 'key': 'consulting_area_1_desc', 'label': 'Advisory Area 1 Description', 'location_hint': 'Practices: Card 01 description', 'default_value': 'Structuring institutional PMO frameworks, steering committee reporting cadences, and stage-gate approval controls for capital works.', 'is_multiline': True},
        {'page': 'consulting', 'key': 'consulting_area_2_title', 'label': 'Advisory Area 2 Title', 'location_hint': 'Practices: Card 02 title', 'default_value': 'Technical Project Auditing', 'is_multiline': False},
        {'page': 'consulting', 'key': 'consulting_area_2_desc', 'label': 'Advisory Area 2 Description', 'location_hint': 'Practices: Card 02 description', 'default_value': 'Rigorous forensic analysis of project baselines, earned value cost integrity, and critical path scheduling slippages before disputes arise.', 'is_multiline': True},
        {'page': 'consulting', 'key': 'consulting_area_3_title', 'label': 'Advisory Area 3 Title', 'location_hint': 'Practices: Card 03 title', 'default_value': 'Project Management Advice', 'is_multiline': False},
        {'page': 'consulting', 'key': 'consulting_area_3_desc', 'label': 'Advisory Area 3 Description', 'location_hint': 'Practices: Card 03 description', 'default_value': 'Confidential counsel for executive sponsors, ministers, and project directors managing troubled contractors, cost overruns, and claims.', 'is_multiline': True},
        {'page': 'consulting', 'key': 'consulting_banner_badge', 'label': 'Contact Banner Badge', 'location_hint': 'Action Banner: Small top tag', 'default_value': 'Direct Contact', 'is_multiline': False},
        {'page': 'consulting', 'key': 'consulting_banner_title', 'label': 'Contact Banner Headline', 'location_hint': 'Action Banner: Main title', 'default_value': 'Speak directly with Director awuah', 'is_multiline': False},
        {'page': 'consulting', 'key': 'consulting_banner_desc', 'label': 'Contact Banner Description', 'location_hint': 'Action Banner: Subtitle paragraph', 'default_value': 'For confidential institutional advisory, corporate audits, or steering committee requests, reach Director awuah directly via the Directorate advisory desk.', 'is_multiline': True},

        # Department Under-Construction Locks
        {'page': 'corporate', 'key': 'lock_corporate', 'label': 'Corporate Training Availability Lock', 'location_hint': 'Department Lock Status', 'default_value': '0', 'is_multiline': False},
        {'page': 'certifications', 'key': 'lock_certifications', 'label': 'Certifications Availability Lock', 'location_hint': 'Department Lock Status', 'default_value': '0', 'is_multiline': False},
        {'page': 'consulting', 'key': 'lock_consulting', 'label': 'Consulting Availability Lock', 'location_hint': 'Department Lock Status', 'default_value': '1', 'is_multiline': False},
    ]

    for item in DEFAULT_SNIPPETS:
        snip, created = SiteSnippet.objects.get_or_create(key=item['key'], defaults=item)
        if not created and snip.default_value != item['default_value']:
            if snip.value in ['Welcome to the home of', 'cutting-edge project management.', 'Systems Thinking in Action: Inside Project Focus']:
                snip.value = ''
            snip.default_value = item['default_value']
            snip.label = item['label']
            snip.save()

    # Process save, preview staging, publish, or revert actions
    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        # Action 1: Stage draft in private session and open preview
        if action == 'preview_draft':
            draft = request.session.get('site_editor_draft', {})
            for key, val in request.POST.items():
                if key.startswith('snippet_'):
                    snip_id = key.replace('snippet_', '')
                    snippet = SiteSnippet.objects.filter(id=snip_id).first()
                    if snippet:
                        draft[snippet.key] = val.strip()

            active_tab = request.POST.get('active_tab', 'home')
            if active_tab in ['corporate', 'certifications', 'consulting']:
                draft[f"lock_{active_tab}"] = '1' if request.POST.get('is_dept_locked') == '1' else '0'

            # Stage newly uploaded video in session preview
            if 'executive_video' in request.FILES:
                v_file = request.FILES['executive_video']
                success, v_result = handle_executive_video_upload(v_file)
                if success:
                    draft['home_video_file'] = v_result
                    messages.success(request, f"Staged new video preview ({v_file.size / (1024*1024):.1f}MB).")
                else:
                    messages.error(request, v_result)

            request.session['site_editor_draft'] = draft
            request.session['site_editor_preview'] = True

            # Track the spotlight key and return URL for live site actions
            spotlight_key = request.POST.get('spotlight_key', '').strip()
            request.session['spotlight_key'] = spotlight_key

            active_tab = request.POST.get('active_tab', 'home')
            request.session['preview_active_tab'] = active_tab

            preview_target = request.POST.get('preview_target')
            if not preview_target:
                tab_url_map = {
                    'home': reverse('courses:home'),
                    'about': reverse('courses:about'),
                    'corporate': reverse('courses:all_programs'),
                    'certifications': reverse('courses:certifications'),
                    'consulting': reverse('courses:consulting'),
                }
                preview_target = tab_url_map.get(active_tab, reverse('courses:home'))

            clean_live_url = preview_target.split('#')[0]
            request.session['preview_return_url'] = clean_live_url
            request.session.modified = True

            # Route directly to the targeted snippet anchor if set
            if spotlight_key and '#snippet-' not in preview_target:
                preview_target = f"{clean_live_url}#snippet-{spotlight_key}"

            messages.info(request, "Draft staged in preview mode. Regular visitors still see the live site.")
            return redirect(preview_target)

        # Action 2: Commit staged session draft to database
        elif action == 'publish_draft':
            draft = request.session.get('site_editor_draft', {})
            published_count = 0
            for k, v in draft.items():
                snippet = SiteSnippet.objects.filter(key=k).first()
                if snippet:
                    clean_val = v.strip() if v else ''
                    snippet.value = '' if clean_val == snippet.default_value.strip() else clean_val
                    snippet.save()
                    published_count += 1

            active_tab = request.session.get('preview_active_tab', 'home')
            request.session['site_editor_draft'] = {}
            request.session['site_editor_preview'] = False
            request.session['spotlight_key'] = ''
            request.session.modified = True
            messages.success(request, f"Published {published_count} draft text updates to the live site.")
            return redirect(f"{reverse('courses:director_site_editor')}?tab={active_tab}")

        # Action 2b: Stage course specifications into session and open preview
        elif action == 'preview_course':
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id)
            new_weeks = int(request.POST.get('duration_weeks', course.duration_weeks) or course.duration_weeks)
            new_unit = request.POST.get('duration_unit', course.duration_unit or 'weeks')
            new_hours = int(request.POST.get('contact_hours', course.contact_hours) or course.contact_hours)
            new_fee = float(request.POST.get('fee', course.fee) or course.fee)
            new_schedule = request.POST.get('schedule_details', course.schedule_details or '').strip()
            new_tagline = request.POST.get('tagline', course.tagline or '').strip()
            new_overview = request.POST.get('overview', course.overview or '').strip()
            new_deliverables = request.POST.get('deliverables', course.deliverables or '').strip()
            new_under_construction = request.POST.get('is_under_construction') == '1'

            # Resolve baseline against existing session draft first, falling back to database
            base_draft = request.session.get('course_editor_draft') or {}
            if base_draft.get('course_id') == course.id:
                base_fee = float(base_draft.get('fee', course.fee) or 0)
                base_hours = int(base_draft.get('contact_hours', course.contact_hours) or 0)
                base_weeks = int(base_draft.get('duration_weeks', course.duration_weeks) or 0)
                base_unit = base_draft.get('duration_unit', course.duration_unit or 'weeks')
                base_sched = (base_draft.get('schedule_details', course.schedule_details) or '').strip()
                base_tagline = (base_draft.get('tagline', course.tagline) or '').strip()
                base_overview = (base_draft.get('overview', course.overview) or '').strip()
                base_deliv = (base_draft.get('deliverables', course.deliverables) or '').strip()
            else:
                base_fee = float(course.fee or 0)
                base_hours = int(course.contact_hours or 0)
                base_weeks = int(course.duration_weeks or 0)
                base_unit = course.duration_unit or 'weeks'
                base_sched = (course.schedule_details or '').strip()
                base_tagline = (course.tagline or '').strip()
                base_overview = (course.overview or '').strip()
                base_deliv = (course.deliverables or '').strip()

            course_draft = {
                'course_id': course.id,
                'duration_weeks': new_weeks,
                'duration_unit': new_unit,
                'contact_hours': new_hours,
                'fee': new_fee,
                'schedule_details': new_schedule,
                'tagline': new_tagline,
                'overview': new_overview,
                'deliverables': new_deliverables,
                'is_under_construction': new_under_construction,
            }
            request.session['course_editor_draft'] = course_draft
            request.session['site_editor_preview'] = True
            request.session['preview_active_tab'] = 'courses'
            request.session['preview_course_id'] = course.id

            # Detect which deliverable line changed if deliverables were edited
            orig_deliv_list = [line.strip() for line in base_deliv.splitlines() if line.strip()]
            new_deliv_list = [line.strip() for line in new_deliverables.splitlines() if line.strip()]

            changed_deliv_idx = 1
            for idx, (new_it, orig_it) in enumerate(zip(new_deliv_list, orig_deliv_list), start=1):
                if new_it != orig_it:
                    changed_deliv_idx = idx
                    break
            else:
                if len(new_deliv_list) > len(orig_deliv_list):
                    changed_deliv_idx = len(orig_deliv_list) + 1
                elif len(new_deliv_list) < len(orig_deliv_list):
                    changed_deliv_idx = max(1, len(new_deliv_list))
                else:
                    changed_deliv_idx = 1

            # Prioritize genuine field differences over stale hidden input values
            detected_field = None
            if new_hours != base_hours:
                detected_field = 'course-hours'
            elif new_weeks != base_weeks or new_unit != base_unit:
                detected_field = 'course-duration'
            elif new_schedule != base_sched:
                detected_field = 'course-schedule'
            elif abs(new_fee - base_fee) > 0.01:
                detected_field = 'course-fee'
            elif new_tagline != base_tagline:
                detected_field = 'course-tagline'
            elif new_overview != base_overview:
                detected_field = 'course-overview'
            elif new_deliverables != base_deliv:
                detected_field = f'course-deliverable-{changed_deliv_idx}'

            posted_field = request.POST.get('spotlight_field', '').strip()
            if posted_field == 'course-deliverables':
                posted_field = f'course-deliverable-{changed_deliv_idx}'

            target_field = detected_field or posted_field or 'course-duration'

            request.session['spotlight_key'] = target_field
            request.session.modified = True

            messages.info(request, f"Previewing staged specifications for '{course.title}'.")
            return redirect(f"{reverse('courses:detail', args=[course.slug])}#snippet-{target_field}")
        # Action 2c: Stage module curriculum draft into session and preview in classroom
        elif action == 'preview_module':
            module_id = request.POST.get('module_id')
            course_module = get_object_or_404(CourseModule, id=module_id)

            new_title = request.POST.get('title', course_module.title).strip()
            new_synopsis = request.POST.get('synopsis', course_module.synopsis).strip()
            new_slide_url = request.POST.get('slide_deck_url', course_module.slide_deck_url).strip()
            new_notes = request.POST.get('lecture_notes', course_module.lecture_notes).strip()
            new_task_q = request.POST.get('task_question', course_module.task_question).strip()
            new_task_s = request.POST.get('task_solution', course_module.task_solution).strip()

            module_draft = {
                'module_id': course_module.id,
                'course_id': course_module.course.id,
                'order': course_module.order,
                'title': new_title,
                'synopsis': new_synopsis,
                'slide_deck_url': new_slide_url,
                'lecture_notes': new_notes,
                'task_question': new_task_q,
                'task_solution': new_task_s,
            }
            request.session['module_editor_draft'] = module_draft
            request.session['site_editor_preview'] = True
            request.session['preview_active_tab'] = 'modules'
            request.session['preview_course_id'] = course_module.course.id
            request.session['preview_module_id'] = course_module.id

            # Detect which exact note line was changed if lecture notes were edited
            orig_notes_lines = [l.strip() for l in (course_module.lecture_notes or '').splitlines() if l.strip()]
            new_notes_lines = [l.strip() for l in new_notes.splitlines() if l.strip()]

            changed_note_idx = 1
            for idx, (new_l, orig_l) in enumerate(zip(new_notes_lines, orig_notes_lines), start=1):
                if new_l != orig_l:
                    changed_note_idx = idx
                    break
            else:
                if len(new_notes_lines) > len(orig_notes_lines):
                    changed_note_idx = len(orig_notes_lines) + 1
                elif len(new_notes_lines) < len(orig_notes_lines):
                    changed_note_idx = max(1, len(new_notes_lines))
                else:
                    changed_note_idx = 1

            base_draft = request.session.get('module_editor_draft') or {}
            if base_draft.get('module_id') == course_module.id:
                base_title = (base_draft.get('title', course_module.title) or '').strip()
                base_synopsis = (base_draft.get('synopsis', course_module.synopsis) or '').strip()
                base_slide = (base_draft.get('slide_deck_url', course_module.slide_deck_url) or '').strip()
                base_notes = (base_draft.get('lecture_notes', course_module.lecture_notes) or '').strip()
                base_task_q = (base_draft.get('task_question', course_module.task_question) or '').strip()
                base_task_s = (base_draft.get('task_solution', course_module.task_solution) or '').strip()
            else:
                base_title = (course_module.title or '').strip()
                base_synopsis = (course_module.synopsis or '').strip()
                base_slide = (course_module.slide_deck_url or '').strip()
                base_notes = (course_module.lecture_notes or '').strip()
                base_task_q = (course_module.task_question or '').strip()
                base_task_s = (course_module.task_solution or '').strip()

            # Detect which exact task line was changed if task_question was edited
            orig_task_lines = [l.strip() for l in (course_module.task_question or '').splitlines() if l.strip()]
            new_task_lines = [l.strip() for l in new_task_q.splitlines() if l.strip()]

            changed_task_idx = 1
            for idx, (new_l, orig_l) in enumerate(zip(new_task_lines, orig_task_lines), start=1):
                if new_l != orig_l:
                    changed_task_idx = idx
                    break
            else:
                if len(new_task_lines) > len(orig_task_lines):
                    changed_task_idx = len(orig_task_lines) + 1
                elif len(new_task_lines) < len(orig_task_lines):
                    changed_task_idx = max(1, len(new_task_lines))
                else:
                    changed_task_idx = 1

            # Detect which exact rubric line was changed if task_solution was edited
            orig_rubric_lines = [l.strip() for l in (course_module.task_solution or '').splitlines() if l.strip()]
            new_rubric_lines = [l.strip() for l in new_task_s.splitlines() if l.strip()]

            changed_rubric_idx = 1
            for idx, (new_l, orig_l) in enumerate(zip(new_rubric_lines, orig_rubric_lines), start=1):
                if new_l != orig_l:
                    changed_rubric_idx = idx
                    break
            else:
                if len(new_rubric_lines) > len(orig_rubric_lines):
                    changed_rubric_idx = len(orig_rubric_lines) + 1
                elif len(new_rubric_lines) < len(orig_rubric_lines):
                    changed_rubric_idx = max(1, len(new_rubric_lines))
                else:
                    changed_rubric_idx = 1

            target_field = request.POST.get('spotlight_field', '').strip()
            if target_field == 'module-notes':
                spotlight_anchor = f"module-note-line-{course_module.order}-{changed_note_idx}"
            elif target_field == 'module-tasks':
                spotlight_anchor = f"module-task-line-{course_module.order}-{changed_task_idx}"
            elif target_field == 'module-rubric':
                spotlight_anchor = f"module-rubric-line-{course_module.order}-{changed_rubric_idx}"
            elif not target_field:
                if new_task_s != (course_module.task_solution or '').strip():
                    spotlight_anchor = f"module-rubric-line-{course_module.order}-{changed_rubric_idx}"
                elif new_task_q != (course_module.task_question or '').strip():
                    spotlight_anchor = f"module-task-line-{course_module.order}-{changed_task_idx}"
                elif new_notes != (course_module.lecture_notes or '').strip():
                    spotlight_anchor = f"module-note-line-{course_module.order}-{changed_note_idx}"
                elif new_slide_url != (course_module.slide_deck_url or '').strip():
                    spotlight_anchor = f"module-slides-{course_module.order}"
                elif new_synopsis != (course_module.synopsis or '').strip() and new_title == (course_module.title or '').strip():
                    spotlight_anchor = f"module-synopsis-{course_module.order}"
                elif new_title != (course_module.title or '').strip():
                    spotlight_anchor = f"module-title-{course_module.order}"
                else:
                    spotlight_anchor = f"module-task-line-{course_module.order}-{changed_task_idx}"
            else:
                spotlight_anchor = f"{target_field}-{course_module.order}"

            request.session['spotlight_key'] = spotlight_anchor
            request.session.modified = True

            messages.info(request, f"Previewing Module {course_module.order} in Classroom Hub.")
            return redirect(f"{reverse('courses:classroom', args=[course_module.course.slug])}?module={course_module.order}#snippet-{spotlight_anchor}")

        # Action 3: Discard staged session draft and return directly to editor console
        elif action == 'discard_draft':
            active_tab = request.session.get('preview_active_tab', 'home')
            course_id = request.session.get('preview_course_id')
            module_id = request.session.get('preview_module_id')
            request.session['site_editor_draft'] = {}
            request.session['course_editor_draft'] = {}
            request.session['module_editor_draft'] = {}
            request.session['site_editor_preview'] = False
            request.session['spotlight_key'] = ''
            request.session.modified = True
            messages.info(request, "Draft discarded. All texts, specifications, and module curricula reverted.")
            redirect_url = f"{reverse('courses:director_site_editor')}?tab={active_tab}"
            if active_tab == 'courses' and course_id:
                redirect_url += f"&course_id={course_id}"
            elif active_tab == 'modules' and course_id and module_id:
                redirect_url += f"&course_id={course_id}&module_id={module_id}"
            return redirect(redirect_url)

        # Action 4: Revert a specific snippet to factory default
        elif action == 'revert':
            snippet_id = request.POST.get('snippet_id')
            snippet = SiteSnippet.objects.filter(id=snippet_id).first()
            if snippet:
                snippet.value = ''
                snippet.save()
                messages.success(request, f"'{snippet.label}' reverted to factory default.")
            return redirect(f"{reverse('courses:director_site_editor')}?tab={snippet.page if snippet else 'home'}")

        # Action 5: Save updated texts directly
        elif action == 'save':
            updated_count = 0
            for key, val in request.POST.items():
                if key.startswith('snippet_'):
                    snip_id = key.replace('snippet_', '')
                    snippet = SiteSnippet.objects.filter(id=snip_id).first()
                    if snippet:
                        clean_val = val.strip()
                        snippet.value = '' if clean_val == snippet.default_value.strip() else clean_val
                        snippet.save()
                        updated_count += 1

            # Save practice department lock toggle if editing Corporate, Certifications, or Consulting
            active_tab = request.POST.get('active_tab', 'home')
            if active_tab in ['corporate', 'certifications', 'consulting']:
                lock_snip = SiteSnippet.objects.filter(key=f"lock_{active_tab}").first()
                if lock_snip:
                    is_locked = request.POST.get('is_dept_locked') == '1'
                    lock_snip.value = '1' if is_locked else '0'
                    lock_snip.save()

            # Process direct video file upload or commit staged video from preview session
            if 'executive_video' in request.FILES:
                v_file = request.FILES['executive_video']
                success, v_result = handle_executive_video_upload(v_file)
                if success:
                    v_snip = SiteSnippet.objects.filter(key='home_video_file').first()
                    if v_snip:
                        v_snip.value = v_result
                        v_snip.save()
                        updated_count += 1
                    messages.success(request, f"New video published live ({v_file.size / (1024*1024):.1f}MB).")
                else:
                    messages.error(request, v_result)
            elif request.session.get('site_editor_draft', {}).get('home_video_file'):
                staged_url = request.session['site_editor_draft']['home_video_file']
                v_snip = SiteSnippet.objects.filter(key='home_video_file').first()
                if v_snip:
                    v_snip.value = staged_url
                    v_snip.save()
                    updated_count += 1

            # Fully flush preview mode and staged session drafts on live publication
            request.session.pop('site_editor_preview', None)
            request.session.pop('site_editor_draft', None)
            request.session.pop('spotlight_key', None)
            request.session.pop('preview_return_url', None)
            request.session.pop('preview_active_tab', None)
            request.session.modified = True

            messages.success(request, f"Saved {updated_count} text and availability changes successfully.")
            return redirect(f"{reverse('courses:director_site_editor')}?tab={active_tab}")
        # Action 6: Update course duration, hours, fee, overview, deliverables & construction state
        elif action == 'update_course':
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id)
            course.duration_weeks = int(request.POST.get('duration_weeks', course.duration_weeks) or course.duration_weeks)
            course.duration_unit = request.POST.get('duration_unit', course.duration_unit)
            course.contact_hours = int(request.POST.get('contact_hours', course.contact_hours) or course.contact_hours)
            course.fee = float(request.POST.get('fee', course.fee) or course.fee)
            course.schedule_details = request.POST.get('schedule_details', course.schedule_details).strip()
            course.tagline = request.POST.get('tagline', course.tagline).strip()
            course.overview = request.POST.get('overview', course.overview).strip()
            course.deliverables = request.POST.get('deliverables', course.deliverables).strip()
            course.is_under_construction = request.POST.get('is_under_construction') == '1'
            course.save()

            # Clear staged course draft and exit preview mode upon live save
            request.session.pop('course_editor_draft', None)
            request.session.pop('preview_course_id', None)
            request.session.pop('site_editor_preview', None)
            request.session.pop('spotlight_key', None)
            request.session.modified = True

            messages.success(request, f"Course specifications for '{course.title}' updated successfully.")
            return redirect(f"{reverse('courses:director_site_editor')}?tab=courses&course_id={course.id}")

        # Action 7: Update classroom module content
        elif action == 'update_module':
            module_id = request.POST.get('module_id')
            course_module = get_object_or_404(CourseModule, id=module_id)
            course_module.title = request.POST.get('title', course_module.title).strip()
            course_module.synopsis = request.POST.get('synopsis', course_module.synopsis).strip()
            course_module.slide_deck_url = request.POST.get('slide_deck_url', course_module.slide_deck_url).strip()
            course_module.lecture_notes = request.POST.get('lecture_notes', course_module.lecture_notes).strip()
            course_module.task_question = request.POST.get('task_question', course_module.task_question).strip()
            course_module.task_solution = request.POST.get('task_solution', course_module.task_solution).strip()
            course_module.save()

            # Clear staged module draft and exit preview mode upon live save
            request.session.pop('module_editor_draft', None)
            request.session.pop('preview_module_id', None)
            request.session.pop('site_editor_preview', None)
            request.session.pop('spotlight_key', None)
            request.session.modified = True

            messages.success(request, f"Module {course_module.order} ('{course_module.clean_title}') updated successfully.")
            return redirect(f"{reverse('courses:director_site_editor')}?tab=modules&course_id={course_module.course.id}&module_id={course_module.id}")

    # Fallback to preview tab if returning from preview (Gracefully redirect obsolete modules tab)
    active_tab = request.GET.get('tab')
    if not active_tab and request.GET.get('from_preview'):
        active_tab = request.session.get('preview_active_tab', 'home')
    elif not active_tab or active_tab == 'modules':
        active_tab = 'home'

    # Filter text snippets excluding lock toggles and video file URL (handled via dedicated uploader)
    active_snippets = SiteSnippet.objects.filter(page=active_tab).exclude(key__startswith='lock_').exclude(key='home_video_file')

    # Resolve active video URL for homepage video manager card
    video_snip = SiteSnippet.objects.filter(key='home_video_file').first()
    current_video_url = (video_snip.value or video_snip.default_value) if video_snip else '/media/MA.mp4'
    if request.session.get('site_editor_draft', {}).get('home_video_file'):
        current_video_url = request.session['site_editor_draft']['home_video_file']

    # Resolve practice department lock status for UI pills and switches
    lock_corp = SiteSnippet.objects.filter(key='lock_corporate').first()
    lock_corporate = (lock_corp.value or lock_corp.default_value) == '1' if lock_corp else False

    lock_certs = SiteSnippet.objects.filter(key='lock_certifications').first()
    lock_certifications = (lock_certs.value or lock_certs.default_value) == '1' if lock_certs else False

    lock_cons = SiteSnippet.objects.filter(key='lock_consulting').first()
    lock_consulting = (lock_cons.value or lock_cons.default_value) == '1' if lock_cons else True

    is_dept_locked = False
    if active_tab == 'corporate':
        is_dept_locked = lock_corporate
    elif active_tab == 'certifications':
        is_dept_locked = lock_certifications
    elif active_tab == 'consulting':
        is_dept_locked = lock_consulting

    # Course Specifications Data (All Practice Areas)
    all_courses = Course.objects.filter(is_active=True).select_related('category').order_by('category__slug', 'title')

    selected_course_id = request.GET.get('course_id') or (str(request.session.get('preview_course_id')) if active_tab == 'courses' else None)
    
    selected_course = None
    if selected_course_id and str(selected_course_id).isdigit():
        selected_course = all_courses.filter(id=int(selected_course_id)).first()

    if not selected_course and all_courses.exists():
        selected_course = all_courses.first()

    # Populate selected course in-memory with staged preview draft if returning
    if selected_course and request.session.get('course_editor_draft'):
        c_draft = request.session['course_editor_draft']
        if c_draft.get('course_id') == selected_course.id:
            selected_course.duration_weeks = c_draft.get('duration_weeks', selected_course.duration_weeks)
            selected_course.duration_unit = c_draft.get('duration_unit', selected_course.duration_unit)
            selected_course.contact_hours = c_draft.get('contact_hours', selected_course.contact_hours)
            selected_course.fee = c_draft.get('fee', selected_course.fee)
            selected_course.schedule_details = c_draft.get('schedule_details', selected_course.schedule_details)
            selected_course.tagline = c_draft.get('tagline', selected_course.tagline)
            selected_course.overview = c_draft.get('overview', selected_course.overview)
            selected_course.deliverables = c_draft.get('deliverables', selected_course.deliverables)
            if 'is_under_construction' in c_draft:
                selected_course.is_under_construction = c_draft['is_under_construction']

    # Auto-provision full 20 modules in database if course has fewer than 20
    if selected_course and selected_course.modules.count() < 20:
        base_list = selected_course.get_modules_list()
        while len(base_list) < 20:
            base_list.append(f"Advanced Systems Execution Part {len(base_list) + 1}")
        existing_orders = set(selected_course.modules.values_list('order', flat=True))
        new_modules = []
        for idx in range(1, 21):
            if idx not in existing_orders:
                title = base_list[idx - 1]
                new_modules.append(CourseModule(
                    course=selected_course,
                    order=idx,
                    title=title,
                    synopsis=f"PMBOK® 8th Edition executive delivery mechanics and systems governance framework for {title}.",
                    lecture_notes=(
                        f"PMBOK® Guide 8th Edition Strategic Outline — Module {idx:02d}: {title}\n"
                        f"• Systems Thinking & Value Delivery Networks: Aligning operational throughput with enterprise strategy.\n"
                        f"• AI-Assisted Project Telemetry: Leveraging machine learning heuristics for schedule variance and risk sensing.\n"
                        f"• Next-Gen Hybrid Governance: Harmonizing predictive compliance gates with adaptive value-stream cadences.\n"
                        f"• ESG & Sustainable Stewardship: Verifying statutory, environmental, and ethical baselines in contract execution."
                    ),
                    is_preview=(idx == 1)
                ))
        if new_modules:
            CourseModule.objects.bulk_create(new_modules)

    course_modules = selected_course.modules.all().order_by('order') if selected_course else []
    selected_module_id = request.GET.get('module_id') or (str(request.session.get('preview_module_id')) if active_tab == 'modules' else None)
    selected_module = None
    if selected_module_id and str(selected_module_id).isdigit():
        selected_module = course_modules.filter(id=int(selected_module_id)).first()
    if not selected_module and course_modules.exists():
        selected_module = course_modules.first()

    # Re-populate selected module in-memory with staged preview draft if returning
    if selected_module and request.session.get('module_editor_draft'):
        m_draft = request.session['module_editor_draft']
        if m_draft.get('module_id') == selected_module.id:
            selected_module.title = m_draft.get('title', selected_module.title)
            selected_module.synopsis = m_draft.get('synopsis', selected_module.synopsis)
            selected_module.slide_deck_url = m_draft.get('slide_deck_url', selected_module.slide_deck_url)
            selected_module.lecture_notes = m_draft.get('lecture_notes', selected_module.lecture_notes)
            selected_module.task_question = m_draft.get('task_question', selected_module.task_question)
            selected_module.task_solution = m_draft.get('task_solution', selected_module.task_solution)

    context = {
        'active_tab': active_tab,
        'active_snippets': active_snippets,
        'all_courses': all_courses,
        'selected_course': selected_course,
        'course_modules': course_modules,
        'selected_module': selected_module,
        'draft_snippets': request.session.get('site_editor_draft', {}),
        'lock_corporate': lock_corporate,
        'lock_certifications': lock_certifications,
        'lock_consulting': lock_consulting,
        'is_dept_locked': is_dept_locked,
        'is_preview_mode': False,
        'returned_from_preview': bool(request.GET.get('from_preview')),
        'has_staged_draft': bool(request.session.get('site_editor_draft')) or bool(request.session.get('course_editor_draft')) or bool(request.session.get('module_editor_draft')),
    }
    return render(request, 'director_site_editor.html', context)


def director_assessment_desk_view(request):
    """
    Dedicated Question Bank & MCQ Studio for Director Mike Awuah.
    Restricted strictly to staff/director accounts.
    Allows managing MCQs per module and testing the simulator.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return redirect('courses:mike_login')

    all_courses = Course.objects.filter(is_active=True, category__slug='certifications').prefetch_related('modules').order_by('title')
    course_id = request.GET.get('course_id') or request.POST.get('course_id')
    selected_course = None
    if course_id and str(course_id).isdigit():
        selected_course = all_courses.filter(id=int(course_id)).first()
    if not selected_course and all_courses.exists():
        selected_course = all_courses.first()

    course_modules = selected_course.modules.all().prefetch_related('mcq_questions').order_by('order') if selected_course else []
    module_id = request.GET.get('module_id') or request.POST.get('module_id')
    selected_module = None
    if module_id and str(module_id).isdigit():
        selected_module = course_modules.filter(id=int(module_id)).first()
    if not selected_module and course_modules.exists():
        selected_module = course_modules.first()

    # Handle manual add / edit / delete question
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_question' and selected_module:
            q_id = request.POST.get('question_id')
            q_text = request.POST.get('question_text', '').strip()
            opt_a = request.POST.get('option_a', '').strip()
            opt_b = request.POST.get('option_b', '').strip()
            opt_c = request.POST.get('option_c', '').strip()
            opt_d = request.POST.get('option_d', '').strip()
            correct = request.POST.get('correct_option', 'A').strip().upper()
            expl = request.POST.get('explanation', '').strip()

            if q_id and q_id.isdigit():
                question = get_object_or_404(ModuleQuestion, id=int(q_id), module=selected_module)
                question.question_text = q_text
                question.option_a = opt_a
                question.option_b = opt_b
                question.option_c = opt_c
                question.option_d = opt_d
                question.correct_option = correct
                question.explanation = expl
                question.save()
                messages.success(request, f"Question {question.order} updated successfully.")
            else:
                next_order = selected_module.mcq_questions.count() + 1
                question = ModuleQuestion.objects.create(
                    module=selected_module,
                    order=next_order,
                    question_text=q_text,
                    option_a=opt_a,
                    option_b=opt_b,
                    option_c=opt_c,
                    option_d=opt_d,
                    correct_option=correct,
                    explanation=expl
                )
                messages.success(request, f"New Question {question.order} added successfully.")

            return redirect(f"{reverse('courses:director_assessment_desk')}?course_id={selected_course.id}&module_id={selected_module.id}")

        elif action == 'delete_question':
            q_id = request.POST.get('question_id')
            if q_id and q_id.isdigit():
                question = get_object_or_404(ModuleQuestion, id=int(q_id))
                m_id = question.module_id
                c_id = question.module.course_id
                question.delete()
                messages.info(request, "Question deleted.")
                return redirect(f"{reverse('courses:director_assessment_desk')}?course_id={c_id}&module_id={m_id}")

    questions = selected_module.mcq_questions.all().order_by('order') if selected_module else []
    append_warning = request.session.pop('mcq_append_warning', None)

    context = {
        'all_courses': all_courses,
        'selected_course': selected_course,
        'course_modules': course_modules,
        'selected_module': selected_module,
        'questions': questions,
        'append_warning': append_warning,
    }
    return render(request, 'courses/assessment_desk.html', context)


@require_POST
def bulk_upload_mcq_view(request):
    """
    Ingests .docx or .pdf, parses MCQs, prompts append confirmation if questions exist,
    and bulk-appends them upon confirmation.
    """
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access.'}, status=403)

    module_id = request.POST.get('module_id')
    course_module = get_object_or_404(CourseModule, id=module_id)
    confirm_append = request.POST.get('confirm_append') == '1'

    doc_file = request.FILES.get('document')
    if not doc_file and not request.session.get('pending_mcq_upload'):
        messages.error(request, "Please select a valid .docx or .pdf file to upload.")
        return redirect(f"{reverse('courses:director_assessment_desk')}?course_id={course_module.course.id}&module_id={course_module.id}")

    if doc_file:
        parsed_questions = parse_mcq_document(doc_file)
        if not parsed_questions:
            messages.error(request, "No questions with valid options (A, B, C, D) could be extracted from this document.")
            return redirect(f"{reverse('courses:director_assessment_desk')}?course_id={course_module.course.id}&module_id={course_module.id}")
        request.session['pending_mcq_upload'] = {
            'module_id': course_module.id,
            'questions': parsed_questions,
            'filename': doc_file.name
        }
    else:
        pending = request.session.get('pending_mcq_upload', {})
        parsed_questions = pending.get('questions', [])

    existing_count = course_module.mcq_questions.count()

    # If questions already exist and Mike hasn't confirmed yet, prompt confirmation
    if existing_count > 0 and not confirm_append:
        request.session['mcq_append_warning'] = {
            'module_id': course_module.id,
            'existing_count': existing_count,
            'new_count': len(parsed_questions),
            'filename': request.session.get('pending_mcq_upload', {}).get('filename', 'document')
        }
        return redirect(f"{reverse('courses:director_assessment_desk')}?course_id={course_module.course.id}&module_id={course_module.id}")

    # Mike confirmed or module was empty: bulk append
    start_order = existing_count + 1
    new_objs = []
    for idx, q_data in enumerate(parsed_questions, start=start_order):
        new_objs.append(ModuleQuestion(
            module=course_module,
            order=idx,
            question_text=q_data['question_text'],
            option_a=q_data['option_a'],
            option_b=q_data['option_b'],
            option_c=q_data['option_c'],
            option_d=q_data['option_d'],
            correct_option=q_data.get('correct_option', 'A'),
            explanation=q_data.get('explanation', ''),
        ))

    ModuleQuestion.objects.bulk_create(new_objs)
    request.session.pop('pending_mcq_upload', None)
    request.session.pop('mcq_append_warning', None)

    messages.success(request, f"Successfully appended {len(new_objs)} questions to Module {course_module.order}. (Total: {existing_count + len(new_objs)} questions)")
    return redirect(f"{reverse('courses:director_assessment_desk')}?course_id={course_module.course.id}&module_id={course_module.id}")