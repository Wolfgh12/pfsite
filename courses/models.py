import uuid
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(models.Model):
    class Level(models.TextChoices):
        FUNDAMENTALS = 'fundamentals', 'Fundamentals'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    class DeliveryMode(models.TextChoices):
        WEEKEND_INTENSIVE = 'WEEKEND', 'Weekend Intensive'
        EVENING_TRACK = 'EVENING', 'Weekday Evening Track'
        HYBRID = 'HYBRID', 'Hybrid (In-person & Virtual)'
        ONLINE_LIVE = 'ONLINE', 'Instructor-Led Virtual'

    class DurationUnit(models.TextChoices):
        DAYS = 'days', 'Days'
        WEEKS = 'weeks', 'Weeks'

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='courses')
    level = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.FUNDAMENTALS,
        help_text="Course tier: Fundamentals, Intermediate, or Advanced"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    tagline = models.CharField(
        max_length=255, 
        help_text="Short headline, e.g. 'Aligned with PMBOK 7th Edition & Agile Practice Guide'"
    )
    overview = models.TextField(help_text="Comprehensive course summary focusing on field delivery.")
    contact_hours = models.PositiveIntegerField(default=35, help_text="Accredited PMI contact hours or PDUs.")
    duration_weeks = models.PositiveIntegerField(default=8, help_text="Duration count (e.g. 2, 3, 8).")
    duration_unit = models.CharField(
        max_length=10,
        choices=DurationUnit.choices,
        default=DurationUnit.WEEKS,
        help_text="Unit of duration: Days or Weeks"
    )
    delivery_mode = models.CharField(
        max_length=20, 
        choices=DeliveryMode.choices, 
        default=DeliveryMode.WEEKEND_INTENSIVE
    )

    @property
    def formatted_duration(self):
        """Returns clean human-readable duration, e.g. '2 Days', '1 Day', '3 Weeks', or '1 Week'."""
        val = self.duration_weeks
        if self.duration_unit == self.DurationUnit.DAYS:
            return f"{val} Day" if val == 1 else f"{val} Days"
        return f"{val} Week" if val == 1 else f"{val} Weeks"
    schedule_details = models.CharField(
        max_length=150, 
        help_text="e.g. 'Saturdays: 9:00 AM – 3:00 PM GMT'"
    )
    deliverables = models.TextField(
        help_text="Core takeaways, one per line (e.g. '35 Approved PMI Contact Hours', 'EVM Spreadsheet Models')."
    )
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Tuition fee.")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_deliverables_list(self):
        return [item.strip() for item in self.deliverables.splitlines() if item.strip()]

    def get_modules_list(self):
        # Master 20-Module PMBOK 8th Edition Curriculum Sequence
        master_20 = [
            "Project Management Foundations",
            "Project Delivery Approaches",
            "Project Value Delivery",
            "Project Environment",
            "Project Governance",
            "Project Stakeholder Engagement",
            "Project Communications Management",
            "Project Knowledge Management",
            "Project Teaming",
            "Project Team Leadership",
            "Project Methodology and Planning",
            "Project Scope Management",
            "Project Quality Management",
            "Project Resource Management",
            "Project Financial Management",
            "Project Change Management",
            "Project Risk Management",
            "Project Procurement Management",
            "Project Schedule Management",
            "Project Closure",
        ]

        # Specific track focus areas (leads the sequence, then completes up to 20)
        track_specialties = {
            "Leading a Project Team": [
                "Team Formation, Dynamics & Psychological Safety",
                "Situational Leadership & Team Operating Agreements",
                "Conflict De-escalation & Emotional Intelligence in Delivery",
                "Accountability Frameworks & Motivating Cross-Functional Units",
            ],
            "Working Adaptively": [
                "Iterative Delivery Mindsets vs. Predictive Realities",
                "Value Slicing & Backlog Prioritization Mechanics",
                "Kanban Systems, Flow Optimization & Managing WIP",
                "Retrospectives & Fast-Feedback Loops in Volatile Scopes",
            ],
            "Cross-Mentoring in Project Teams": [
                "Bridging Engineering Experience with Modern Digital PMOs",
                "Structured Pair Shadowing & Tacit Knowledge Capture",
                "Institutional Knowledge Retention & Silo Elimination",
                "Continuous Peer Coaching & Skill Elevation Milestones",
            ],
            "Starting a Project": [
                "Business Case Feasibility & Commercial Value Verification",
                "Authoring an Enforceable Project Charter",
                "Stakeholder Identification, Influence & Expectation Grids",
                "Establishing Initial Governance & Executive Sponsor Sign-Off",
            ],
            "Planning a Project": [
                "Scope Decomposition & 100% Rule Work Breakdown Structures (WBS)",
                "Schedule Logic, Precedence Diagramming & Critical Path (CPM)",
                "Cost Baseline Formulation & Bottom-Up Resource Estimating",
                "Integrated Risk Registers & Baseline Defense Strategies",
            ],
            "Executing a Project": [
                "Contractor Coordination & Day-to-Day Delivery Orchestration",
                "Integrated Change Control & Scope Creep Prevention",
                "Quality Assurance Inspections & Deliverable Verification",
                "Field Communication Cadences & Managing Variance in Real-Time",
            ],
            "Closing a Project": [
                "Punch-List Verification & Formal Customer Acceptance Handover",
                "Procurement Closeout, Claims Settlement & Vendor Releases",
                "Post-Project Retrospectives & Documenting Lessons Learned",
                "Administrative Archiving, Asset Handover & Operational Cutover",
            ],
            "Building an Empowered Team Culture": [
                "Psychological Safety, Trust Architectures & Ownership Culture",
                "Decentralized Decision-Making & Delegation Boundaries",
                "Performance Accountability & Removing Team Execution Roadblocks",
                "Recognizing High Impact & Sustaining Morale under Schedule Pressure",
            ],
            "Collaborating in Projects": [
                "Cross-Functional Alignment & Inter-Departmental Dependency Mapping",
                "Virtual, Co-Located & Hybrid Collaboration Operating Models",
                "Joint Problem-Solving Frameworks & Consensus Protocol",
                "Eliminating Silos & Synchronizing Engineering with Commercial Units",
            ],
            "Engaging Project Stakeholders": [
                "Advanced Stakeholder Mapping & Political Landscape Diagnostics",
                "Expectation Alignment & Tailored Executive Engagement Plans",
                "Navigating Sponsor Turnover, Steering Committees & Dissenting Voices",
                "Stakeholder Relationship Governance & Influence Defense",
            ],
            "Managing Project Risk": [
                "Qualitative & Quantitative Risk Modeling (EMV & Monte Carlo Concepts)",
                "Probability-Impact Calibration & Risk Register Optimization",
                "Threat Avoidance, Mitigation & Commercial Opportunity Exploitation",
                "Proactive Trigger Monitoring & Contingency Reserve Management",
            ],
            "Project Performance Management": [
                "Earned Value Management (EVM): CPI, SPI, CV & SV Mechanics",
                "Estimate at Completion (EAC) & To-Complete Performance Index (TCPI)",
                "Variance Root-Cause Analysis & Corrective Action Plans (CAPA)",
                "Boardroom Performance Intervention & Delivery Trend Forecasting",
            ],
            "Project Metrics and Reporting": [
                "Designing Executive PMO Dashboards & Practical KPI Scorecards",
                "Separating Vanity Metrics from Actionable Delivery Telemetry",
                "Automated Reporting Cadences & Visual Variance Status Summaries",
                "Executive Briefings: Reporting Reality to Steering Committees",
            ],
            "Managing Project Knowledge": [
                "Explicit vs. Tacit Knowledge Capture & Retention Systems",
                "Establishing Institutional Knowledge Repositories & Playbooks",
                "Post-Phase Retrospectives & Converting Lessons into Standard Operating Procedures",
                "Defending Against Talent Turnover & Mitigating Institutional Memory Loss",
            ],
            "Project Compliance and Sustainability": [
                "Statutory Approvals, Regulatory Standards & Audit Readiness Protocols",
                "Environmental, Social & Governance (ESG) Frameworks in Project Delivery",
                "Sustainable Procurement, Material Integrity & Carbon Baselines",
                "Ethical Governance, Contractual Defensibility & Compliance Gates",
            ],
        }

        # If course has specialized domain modules, start with them and complete up to 20
        if self.title in track_specialties:
            specialized = list(track_specialties[self.title])
            for m in master_20:
                if len(specialized) >= 20:
                    break
                if m not in specialized:
                    specialized.append(m)
            return specialized

        # All certifications (PMP, CAPM, PMI-RMP, PMI-SP) and other courses return the full 20 modules
        return master_20

    def __str__(self):
        return self.title


class Cohort(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='cohorts')
    cohort_code = models.CharField(max_length=50, help_text="e.g. 'PMP-OCT-2026' or 'Cohort 12'")
    start_date = models.DateField()
    end_date = models.DateField()
    max_seats = models.PositiveIntegerField(default=25)
    is_open_for_enrollment = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_date']

    @property
    def registered_count(self):
        """Count confirmed registrations, excluding cancelled applications."""
        return self.registrations.exclude(status=Registration.Status.CANCELLED).count()

    @property
    def seats_remaining(self):
        """Calculates live remaining seats."""
        return max(0, self.max_seats - self.registered_count)

    @property
    def is_full(self):
        """True when registration capacity has reached or exceeded max seats."""
        return self.registered_count >= self.max_seats

    @property
    def is_available(self):
        """Intake is open only if manual flag is true and seats remain."""
        return self.is_open_for_enrollment and not self.is_full

    def close_if_full(self):
        """Automatically flips is_open_for_enrollment to False if max seats are reached."""
        if self.is_full and self.is_open_for_enrollment:
            self.is_open_for_enrollment = False
            self.save(update_fields=['is_open_for_enrollment'])

    def __str__(self):
        return f"{self.course.title} - {self.cohort_code} ({self.seats_remaining}/{self.max_seats} seats left)"


class Registration(models.Model):
    class ExperienceLevel(models.TextChoices):
        EARLY = '0-2', '0 - 2 Years (Early Career)'
        MID = '3-5', '3 - 5 Years (Supervisor / Mid-Level)'
        SENIOR = '5-10', '5 - 10 Years (Senior Manager / Lead)'
        EXECUTIVE = '10+', '10+ Years (Director / Executive)'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        CONTACTED = 'CONTACTED', 'Candidate Contacted'
        ADMITTED = 'ADMITTED', 'Admitted to Cohort'
        COMPLETED = 'COMPLETED', 'Graduated'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PARTIAL = 'PARTIAL', 'Deposit / Partial Payment'
        PAID = 'PAID', 'Fully Paid'
        SPONSORED = 'SPONSORED', 'Corporate Sponsored'

    cohort = models.ForeignKey(Cohort, on_delete=models.PROTECT, related_name='registrations')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, help_text="WhatsApp or mobile number")
    organization = models.CharField(max_length=150, blank=True, help_text="Current employer or client organization")
    experience_level = models.CharField(
        max_length=10, 
        choices=ExperienceLevel.choices, 
        default=ExperienceLevel.MID
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(
        max_length=20, 
        choices=PaymentStatus.choices, 
        default=PaymentStatus.UNPAID
    )
    notes = models.TextField(blank=True, help_text="Internal coordinator notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self.cohort.close_if_full()

    def __str__(self):
        return f"{self.full_name} - {self.cohort.cohort_code}"


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    is_from_director = models.BooleanField(
        default=False, 
        help_text="True if sent by awuah/staff, False if sent by the candidate"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        sender = "awuah" if self.is_from_director else self.user.username
        return f"[{sender}] {self.message[:35]}"


class ContactInquiry(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    is_resolved = models.BooleanField(default=False, help_text="Mark when Director/staff has followed up")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"

    def __str__(self):
        return f"{self.full_name} ({self.email}) - {self.created_at.strftime('%d %b %Y')}"


class QuestionTicket(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Under Review'
        ANSWERED = 'ANSWERED', 'Answered'

    ticket_number = models.CharField(
        max_length=32, 
        unique=True, 
        editable=False,
        help_text="Unique tracking reference code (e.g., PF-ASK-8F3A29)"
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    course = models.ForeignKey(
        Course, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='question_tickets',
        help_text="Optional syllabus track associated with the question"
    )
    subject = models.CharField(max_length=200, blank=True, help_text="Inquiry subject or topic")
    question = models.TextField()
    answer = models.TextField(blank=True, help_text="Latest response provided by Director awuah or Directorate staff")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Question Ticket"
        verbose_name_plural = "Question Tickets"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"PF-ASK-{uuid.uuid4().hex[:6].upper()}"
        if self.answer and not self.answered_at:
            self.answered_at = timezone.now()
            self.status = self.Status.ANSWERED
        elif not self.answer:
            self.status = self.Status.PENDING
            self.answered_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.ticket_number}] {self.full_name} ({self.get_status_display()})"


class TicketMessage(models.Model):
    class SenderType(models.TextChoices):
        VISITOR = 'VISITOR', 'Visitor / Candidate'
        DIRECTOR = 'DIRECTOR', 'Director awuah'

    ticket = models.ForeignKey(
        QuestionTicket, 
        on_delete=models.CASCADE, 
        related_name='messages',
        help_text="Inquiry thread this message belongs to"
    )
    sender_type = models.CharField(
        max_length=15, 
        choices=SenderType.choices, 
        default=SenderType.VISITOR
    )
    sender_name = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Ticket Message"
        verbose_name_plural = "Ticket Messages"

    def __str__(self):
        return f"[{self.ticket.ticket_number}][{self.get_sender_type_display()}] {self.message[:35]}"


class CourseModule(models.Model):
    """
    Step-by-Step Module Accordion model holding PowerPoints, videos, notes, tasks, and solutions.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        help_text="Course this module belongs to"
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Sequential position (e.g. 1 for Week 1, 2 for Week 2)"
    )
    title = models.CharField(
        max_length=200,
        help_text="Module title (e.g. 'Module 1: Critical Path & Baseline Formulation')"
    )

    @property
    def clean_title(self):
        """Strips duplicate 'Module XX:' prefixes so sidebar displays cleanly."""
        import re
        return re.sub(r'^Module\s*\d+[:\s-]*', '', self.title, flags=re.IGNORECASE).strip() or self.title
    synopsis = models.TextField(
        blank=True,
        help_text="Brief summary of what this module covers"
    )

    # 1. Video Lecture
    video_url = models.URLField(
        blank=True,
        help_text="Video lecture stream URL (YouTube unlisted, Vimeo, or MP4 link)"
    )

    # 2. PowerPoint / Slide Deck
    slide_deck_file = models.FileField(
        upload_to='course_materials/slides/',
        blank=True,
        null=True,
        help_text="Upload .pptx or .pdf presentation deck"
    )
    slide_deck_url = models.URLField(
        blank=True,
        help_text="Alternative external link (e.g. Google Slides, cloud deck)"
    )

    # 3. Lecture Notes
    lecture_notes = models.TextField(
        blank=True,
        help_text="Full lecture notes, study references, and key takeaways"
    )

    # 4. Task Questions (Holds 20 structured practice/scenario questions)
    task_question = models.TextField(
        blank=True,
        help_text="20 practical tasks, scenario assignments, or domain questions"
    )

    # 5. Model Answers / Solution Key (Holds 20 official rubrics/marking guides)
    task_solution = models.TextField(
        blank=True,
        help_text="20 official model answers, calculation steps, and rubrics"
    )

    is_preview = models.BooleanField(
        default=False,
        help_text="Allow prospective candidates to preview this module for free"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Course Module"
        verbose_name_plural = "Course Modules"

    def get_task_questions_list(self):
        """Returns the 20 practice questions as an iterable list."""
        if not self.task_question:
            return []
        import re
        items = [q.strip() for q in re.split(r'\n(?=(?:Q|Question|Task)?\s*\d+[\.\:\)])', self.task_question) if q.strip()]
        return items if items else [q.strip() for q in self.task_question.splitlines() if q.strip()]

    def get_task_solutions_list(self):
        """Returns the 20 model answers/rubrics as an iterable list."""
        if not self.task_solution:
            return []
        import re
        items = [s.strip() for s in re.split(r'\n(?=(?:Ans|Answer|Solution|Rubric)?\s*\d+[\.\:\)])', self.task_solution) if s.strip()]
        return items if items else [s.strip() for s in self.task_solution.splitlines() if s.strip()]

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"


class SiteSnippet(models.Model):
    """
    Key-Value text snippet store for the Director's non-technical site copy editor.
    Guarantees zero-layout-breakage via fallbacks to hardcoded master text.
    """
    class Page(models.TextChoices):
        HOME = 'home', 'Homepage'
        ABOUT = 'about', 'About Us'
        CORPORATE = 'corporate', 'Corporate Training'
        CERTIFICATIONS = 'certifications', 'Certifications'
        CONSULTING = 'consulting', 'Consulting & Advisory'
        GENERAL = 'general', 'General Site Text'

    page = models.CharField(
        max_length=30,
        choices=Page.choices,
        default=Page.HOME,
        help_text="Website section/page where this snippet belongs"
    )
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Template variable identifier, e.g. 'home_hero_headline'"
    )
    label = models.CharField(
        max_length=200,
        help_text="Simple name for the Director describing what this text is"
    )
    location_hint = models.CharField(
        max_length=255,
        blank=True,
        help_text="Visual explanation of where this text is seen on screen"
    )
    value = models.TextField(
        blank=True,
        help_text="Director's custom text (leave blank to use default)"
    )
    default_value = models.TextField(
        help_text="Original hardcoded template text fallback"
    )
    is_multiline = models.BooleanField(
        default=False,
        help_text="True if this field is a multi-line paragraph rather than a single line title"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['page', 'id']
        verbose_name = "Site Text Snippet"
        verbose_name_plural = "Site Text Snippets"

    @property
    def active_text(self):
        """Returns Director's custom text if available, otherwise returns the master default."""
        return self.value.strip() if self.value and self.value.strip() else self.default_value

    def __str__(self):
        return f"[{self.get_page_display()}] {self.label}"