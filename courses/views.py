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
from .models import Course, Category, Cohort, Registration, ChatMessage, ContactInquiry, QuestionTicket, TicketMessage


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
    
    context = {
        'course': course,
        'open_cohorts': open_cohorts,
        'deliverables': course.get_deliverables_list(),
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

    # Attach tailored 20 questions & model answers, pre-chunked into 5 pages (4 questions per page)
    for m in modules:
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

    # Gate non-preview modules if user is not signed in
    is_locked = False
    if not request.user.is_authenticated and active_module and not active_module.is_preview:
        is_locked = True

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