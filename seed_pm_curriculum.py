import os
import re
from pathlib import Path
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Course, CourseModule

BASE_DIR = Path(__file__).resolve().parent

# -----------------------------------------------------------------------------
# 1. AUTOMATICALLY PATCH TEMPLATES/ALLPROGRAMS.HTML
# -----------------------------------------------------------------------------
def patch_allprograms_html():
    template_path = BASE_DIR / 'templates' / 'allprograms.html'
    if not template_path.exists():
        print(f"[!] Could not find {template_path}")
        return

    content = template_path.read_text(encoding='utf-8')

    # Mapping of courses to their target slugs
    course_slugs = [
        ("Working Adaptively", "working-adaptively"),
        ("Cross-Mentoring in Project Teams", "cross-mentoring-in-project-teams"),
        ("Starting a Project", "starting-a-project"),
        ("Planning a Project", "planning-a-project"),
        ("Executing a Project", "executing-a-project"),
        ("Closing a Project", "closing-a-project"),
        ("Building an Empowered Team Culture", "building-an-empowered-team-culture"),
        ("Collaborating in Projects", "collaborating-in-projects"),
        ("Engaging Project Stakeholders", "engaging-project-stakeholders"),
        ("Managing Project Risk", "managing-project-risk"),
        ("Project Performance Management", "project-performance-management"),
        ("Project Metrics and Reporting", "project-metrics-and-reporting"),
        ("Managing Project Knowledge", "managing-project-knowledge"),
        ("Project Compliance and Sustainability", "project-compliance-and-sustainability"),
    ]

    for title, slug in course_slugs:
        # 1. Update Title link if not already linked
        title_pattern = rf'<h2 class="text-xl font-bold text-white mb-2 leading-snug">\s*{re.escape(title)}\s*</h2>'
        replacement_title = (
            f'<h2 class="text-xl font-bold text-white mb-2 leading-snug">\n'
            f'          <a href="{{% url \'courses:detail\' \'{slug}\' %}}" class="hover:text-sea-cyan transition-colors">\n'
            f'            {title}\n'
            f'          </a>\n'
            f'        </h2>'
        )
        content = re.sub(title_pattern, replacement_title, content)

        # 2. Replace the modal trigger button with the detail page link
        button_pattern = (
            rf'<button type="button"\s+onclick="openRegistrationModal\(\'\',\s*\'{re.escape(title)}\'.*?</button>'
        )
        replacement_button = (
            f'<a href="{{% url \'courses:detail\' \'{slug}\' %}}"\n'
            f'           class="w-full py-2.5 rounded-xl bg-gradient-to-r from-sea-azure via-sea-cyan to-sea-teal text-sea-abyss font-bold text-xs hover:brightness-110 shadow-md shadow-sea-cyan/20 transition-all text-center block">\n'
            f'          View Full Details &amp; Syllabus &rarr;\n'
            f'        </a>'
        )
        content = re.sub(button_pattern, replacement_button, content, flags=re.DOTALL)

    template_path.write_text(content, encoding='utf-8')
    print("✓ Successfully updated all course titles and buttons in templates/allprograms.html")


# -----------------------------------------------------------------------------
# 2. POPULATE MODERN PM CURRICULUM MODULES (CourseModule)
# -----------------------------------------------------------------------------
CURRICULUM_DATA = {
    'leading-a-project-team': [
        {
            'order': 1,
            'title': 'High-Trust Working Agreements & Psychological Safety',
            'synopsis': 'Establishing team charters, psychological safety baselines, and Tuckman maturity models in hybrid delivery.',
            'notes': (
                "1. Tuckman Model in Modern PM: Moving teams from Storming to Performing.\n"
                "2. Amy Edmondson's Psychological Safety Framework: Decoupling fear from failure.\n"
                "3. Authoring Team Charters: Working agreements, core communication hours, and escalation paths."
            ),
            'task': 'Case Scenario: A software and civil engineering unit are clashing on daily standups. Draft a 4-point Team Working Agreement resolving their meeting friction.',
            'solution': 'Model Rubric:\n1. Core collaboration hours defined (10 AM - 3 PM GMT).\n2. Asynchronous status updates via Slack/Jira to replace unnecessary meetings.\n3. Safe disclosure protocol for blocker escalations without blame.\n4. Clear sign-off authority matrix.',
        },
        {
            'order': 2,
            'title': 'Situational Leadership & Conflict De-escalation',
            'synopsis': 'Applying Hersey-Blanchard situational leadership to multidisciplinary talent and resolving interpersonal friction.',
            'notes': (
                "1. Directing vs Coaching vs Supporting vs Delegating across competence levels.\n"
                "2. Interest-Based Relational (IBR) approach to conflict.\n"
                "3. Managing technical specialists who resist traditional PM governance."
            ),
            'task': 'Evaluate a senior architect who bypasses project controls to commit unapproved changes. Outline your situational intervention.',
            'solution': 'Model Rubric:\n1. Move from Delegating to Coaching style.\n2. One-on-one discovery session linking baseline impacts to project risk.\n3. Formalize scope changes through rapid Integrated Change Control (ICC).\n4. Document agreements without alienating key expertise.',
        },
    ],
    'working-adaptively': [
        {
            'order': 1,
            'title': 'Hybrid Frameworks: Blending Predictive Governance with Adaptive Speed',
            'synopsis': 'Integrating PMBOK stage-gates with agile sprint execution, Kanban WIP limits, and rapid feedback loops.',
            'notes': (
                "1. When to use Agile vs Predictive: Cynefin framework applied to project complexity.\n"
                "2. Hybrid delivery models: Fixed budget/milestones with flexible iterative increments.\n"
                "3. Kanban Work-In-Progress (WIP) limit calculations to eliminate bottlenecks."
            ),
            'task': 'A public-sector infrastructure project requires fixed stage-gate audits but wants agile software integration. Design the hybrid governance flow.',
            'solution': 'Model Rubric:\n1. Predictive Stage-Gates at Charter and Procurement milestones.\n2. Bi-weekly Sprint cadences for deliverables with rolling-wave roadmaps.\n3. Sprint reviews mapped to gate compliance deliverables.',
        },
        {
            'order': 2,
            'title': 'Sprint Ceremonies, Team Velocity & Backlog Prioritization',
            'synopsis': 'Running effective standups, backlog refinement, sprint planning, and calculating team velocity.',
            'notes': (
                "1. WSJF (Weighted Shortest Job First) and MoSCoW prioritization methods.\n"
                "2. Measuring Velocity vs Capacity: Avoiding story point inflation.\n"
                "3. Action-oriented Retrospectives: Turning feedback into process improvements."
            ),
            'task': 'Your sprint velocity dropped by 30% over two consecutive sprints due to executive scope injection. Formulate your corrective backlog plan.',
            'solution': 'Model Rubric:\n1. Quantify injected scope impact on the sprint goal.\n2. Present velocity deficit to project sponsor with trade-off choices.\n3. Institute a strict sprint backlog lock with mid-sprint trade-in rules.',
        },
    ],
    'starting-a-project': [
        {
            'order': 1,
            'title': 'Business Case Feasibility & Pre-Project Boundary Defense',
            'synopsis': 'Translating corporate strategic objectives into defensible project boundaries and economic justification.',
            'notes': (
                "1. NPV, ROI, and Payback Period evaluation in business cases.\n"
                "2. Strategic alignment scoring and feasibility stress-testing.\n"
                "3. Defining what is explicitly OUT of scope to prevent early creep."
            ),
            'task': 'Draft the Project Boundaries section for an automated payment gateway integration, explicitly defining 3 in-scope and 3 out-of-scope boundaries.',
            'solution': 'Model Rubric:\nIn-Scope: 1. Paystack card/MoMo processing. 2. Webhook listener. 3. Transaction receipt logging.\nOut-of-Scope: 1. Multi-currency crypto conversion. 2. Manual teller reconciliations. 3. Legacy ERP overhaul.',
        },
        {
            'order': 2,
            'title': 'Executive Project Charter Authoring & Sponsor Sign-Off',
            'synopsis': 'Drafting enforceable project charters, mapping stakeholder power grids, and securing authorized steering sign-off.',
            'notes': (
                "1. Essential components of an executive-grade Project Charter.\n"
                "2. Stakeholder Power/Interest Matrix: Mapping champions vs skeptics.\n"
                "3. Delegated authority levels for the Project Manager (financial and staffing caps)."
            ),
            'task': 'Define the Delegated Authority section of a Project Charter for a $500,000 corporate PMO deployment.',
            'solution': 'Model Rubric:\n1. Up to $15,000 unbudgeted variance approval authority.\n2. Authority to allocate up to 10% schedule contingency without steering committee approval.\n3. Discretionary sign-off on key contractor procurement bids within baseline.',
        },
    ],
    'planning-a-project': [
        {
            'order': 1,
            'title': '100% Rule Work Breakdown Structures (WBS) & Scope Dictionaries',
            'synopsis': 'Decomposing complex deliverables into verifiable work packages without scope gaps or overlaps.',
            'notes': (
                "1. The 100% Rule: Covering all deliverables with zero omitted scope.\n"
                "2. Work package sizing: The 8/80 rule (between 8 and 80 hours of effort).\n"
                "3. Authoring WBS Dictionaries: Acceptance criteria and owner assignment."
            ),
            'task': 'Decompose the "Candidate Admission System" deliverable into 4 distinct, verifiable work packages respecting the 100% rule.',
            'solution': 'Model Rubric:\n1.1 Student Registration API\n1.2 Paystack Gateway Webhook\n1.3 Automated Welcome & Onboarding Dispatcher\n1.4 Admin Dashboard Roster View',
        },
        {
            'order': 2,
            'title': 'Critical Path Method (CPM), Float Defense & Schedule Baselines',
            'synopsis': 'Constructing Precedence Diagramming Method (PDM) schedules, identifying critical path, and defending total float.',
            'notes': (
                "1. Forward and Backward pass calculations: Early Start, Early Finish, Late Start, Late Finish.\n"
                "2. Identifying Zero Total Float on the Critical Path.\n"
                "3. Fast-tracking vs Crashing: Assessing risk vs cost trade-offs."
            ),
            'task': 'Activity B (Duration: 5 days) is on the critical path. Activity C has 8 days of float. A delay of 3 days occurs on Activity B. What is the impact on project completion?',
            'solution': 'Model Rubric:\nBecause Activity B is on the Critical Path with 0 float, any delay on Activity B extends the project end date by exactly 3 days. Crashing or fast-tracking downstream critical path activities is required to recover.',
        },
    ],
    'executing-a-project': [
        {
            'order': 1,
            'title': 'Integrated Change Control (ICC) & Scope Creep Defense',
            'synopsis': 'Enforcing formal change requests, evaluating triple constraint impacts, and governing change control boards.',
            'notes': (
                "1. The 5-step Integrated Change Control process.\n"
                "2. Assessing Cost, Schedule, Quality, and Risk impacts before approving scope modifications.\n"
                "3. Managing Change Control Board (CCB) cadence and client expectation alignment."
            ),
            'task': 'A client requests a "minor" addition of biometric fingerprint scanning mid-project. Walk through your 4-step ICC response.',
            'solution': 'Model Rubric:\n1. Acknowledge request and log into Change Log.\n2. Conduct triple constraint impact analysis (+$12,000 cost, +2 weeks schedule, hardware supply risk).\n3. Submit impact assessment to CCB/client sponsor for formal approval.\n4. If approved, re-baseline schedule and budget; if rejected, archive with documented reasoning.',
        },
    ],
    'closing-a-project': [
        {
            'order': 1,
            'title': 'Client Acceptance Handover & Punch-List Resolution',
            'synopsis': 'Securing formal signed acceptance certificates, clearing outstanding punch-lists, and closing contracts.',
            'notes': (
                "1. Definition of Done (DoD) vs Formal Client Handover.\n"
                "2. Sifting and executing punch-list items with clear acceptance thresholds.\n"
                "3. Procurement contract closeouts and administrative release of warranties."
            ),
            'task': 'Draft a 3-point clause for a Certificate of Practical Completion that shields the project team from uncontracted post-handover requests.',
            'solution': 'Model Rubric:\n1. Formal acknowledgement that all deliverables in WBS Dictionary 1.0 through 4.0 are fully delivered and tested.\n2. Agreement that warranty coverage is restricted strictly to critical bugs for 30 days.\n3. Any enhancement requests beyond signed specs require a separate Phase 2 engagement.',
        },
    ],
    'building-an-empowered-team-culture': [
        {
            'order': 1,
            'title': 'Psychological Safety Architecture & Blameless Retrospectives',
            'synopsis': 'Building a high-accountability culture where project risks and errors are surfaced early without penalty.',
            'notes': (
                "1. Amy Edmondson's 3 pillars of psychological safety in high-stakes delivery.\n"
                "2. Running Blameless Post-Mortems: Focus on systemic process fixes, not scapegoating.\n"
                "3. Establishing clear decision-making thresholds for individual contributors."
            ),
            'task': 'A major database outage was caused by a junior engineer running an unindexed migration. Draft the opening statement for the post-mortem meeting.',
            'solution': 'Model Rubric:\n"We are gathered today to review the failure in our migration pipeline, not the actions of any individual. If our system allowed an unreviewed command to execute in production, that is a failure of our deployment safeguards, not a person. Let us identify the safety gaps and build guardrails."',
        },
    ],
    'managing-project-risk': [
        {
            'order': 1,
            'title': 'Expected Monetary Value (EMV) & Quantitative Risk Modeling',
            'synopsis': 'Calculating probability-weighted financial exposure, setting contingency reserves, and monitoring triggers.',
            'notes': (
                "1. EMV formula: Probability (%) x Impact ($).\n"
                "2. Sizing Contingency Reserves (known unknowns) vs Management Reserves (unknown unknowns).\n"
                "3. Leading risk indicators vs lagging issues."
            ),
            'task': 'Risk A: 30% chance of a $50,000 delay penalty. Risk B: 10% chance of a $100,000 regulatory fine. Calculate total contingency reserve required.',
            'solution': 'Model Rubric:\nEMV(A) = 0.30 x $50,000 = $15,000.\nEMV(B) = 0.10 x $100,000 = $10,000.\nTotal Contingency Reserve required = $15,000 + $10,000 = $25,000.',
        },
    ],
    'project-performance-management': [
        {
            'order': 1,
            'title': 'Earned Value Management (EVM) Mathematical Toolkit',
            'synopsis': 'Calculating Planned Value (PV), Earned Value (EV), Actual Cost (AC), Cost Performance Index (CPI), and Schedule Performance Index (SPI).',
            'notes': (
                "1. EVM Formulas: CV = EV - AC; SV = EV - PV; CPI = EV / AC; SPI = EV / PV.\n"
                "2. Interpreting indices: CPI < 1.0 (over budget); SPI < 1.0 (behind schedule).\n"
                "3. Estimate at Completion (EAC) and To-Complete Performance Index (TCPI) forecasting."
            ),
            'task': 'At Week 4: PV = $40,000, EV = $32,000, AC = $36,000. Calculate CPI, SPI, CV, and SV. State your project status.',
            'solution': 'Model Rubric:\nCPI = $32,000 / $36,000 = 0.89 (Over Budget by 11%)\nSPI = $32,000 / $40,000 = 0.80 (Behind Schedule by 20%)\nCV = -$4,000\nSV = -$8,000\nStatus: Project is simultaneously behind schedule and over budget. Immediate corrective action (CAPA) is required.',
        },
    ],
    'engaging-project-stakeholders': [
        {
            'order': 1,
            'title': 'Power/Interest Mapping & Boardroom Steering Diplomacy',
            'synopsis': 'Diagnosing political landscapes, turning skeptics into advocates, and managing executive expectations.',
            'notes': (
                "1. The 4 Quadrants: High Power/High Interest (Manage Closely), High Power/Low Interest (Keep Satisfied).\n"
                "2. Structuring executive decision briefings in under 3 slides.\n"
                "3. Defusing passive-aggressive resistance from department heads."
            ),
            'task': 'A Finance Director with High Power and Low Interest starts questioning project ROI mid-stream. What is your engagement strategy?',
            'solution': 'Model Rubric:\n1. Transition stakeholder from "Keep Satisfied" to targeted 1-on-1 alignment.\n2. Provide concise, monthly financial telemetry comparing actual burn rate against EVM forecasts.\n3. Involve them in major procurement cost-reduction milestones to provide ownership.',
        },
    ],
    'project-metrics-and-reporting': [
        {
            'order': 1,
            'title': 'PMO Telemetry & Boardroom Scorecard Engineering',
            'synopsis': 'Replacing subjective status reports with data-driven PMO telemetry and automated progress dashboards.',
            'notes': (
                "1. Flaws of subjective RAG (Red/Amber/Green) reports.\n"
                "2. Leading KPIs (Sprint Burndown, Risk Exposure Velocity) vs Lagging KPIs (Cost Incurred).\n"
                "3. Designing executive scorecards for Board of Directors briefings."
            ),
            'task': 'Identify 2 leading indicators and 2 lagging indicators for an infrastructure development initiative.',
            'solution': 'Model Rubric:\nLeading Indicators: 1. Design approval turnaround time. 2. Weekly open site safety hazards reported.\nLagging Indicators: 1. Cumulative cost variance (CV). 2. Total milestone slippage days.',
        },
    ],
    'managing-project-knowledge': [
        {
            'order': 1,
            'title': 'Tacit Knowledge Capture & Institutional SOP Engineering',
            'synopsis': 'Preventing brain-drain, capturing unwritten field heuristics, and converting retrospectives into corporate SOPs.',
            'notes': (
                "1. Explicit Knowledge (docs/manuals) vs Tacit Knowledge (field heuristics, instincts).\n"
                "2. Structured shadowing and technical knowledge debriefs before key personnel depart.\n"
                "3. Institutionalizing retrospective findings into mandatory checklist gates."
            ),
            'task': 'A senior engineering lead is resigning in 3 weeks. Outline your 3-step tacit knowledge extraction plan.',
            'solution': 'Model Rubric:\n1. Pairing with a designated successor for live task shadowing on critical path tasks.\n2. Structured debrief recording architecture decision records (ADRs) for past trade-offs.\n3. Creating a "Known Gotchas" troubleshooting guide for system anomalies.',
        },
    ],
    'project-compliance-and-sustainability': [
        {
            'order': 1,
            'title': 'Statutory Audit Gates & ESG Delivery Baselines',
            'synopsis': 'Integrating environmental, social, and governance (ESG) standards with contractual and regulatory integrity.',
            'notes': (
                "1. Statutory approval workflows and non-negotiable compliance gates.\n"
                "2. ESG baselines: Carbon footprint auditing and fair labor tracking in contractor procurement.\n"
                "3. Contractual integrity: Defending against audit claims and compliance fines."
            ),
            'task': 'Formulate an ESG verification checklist item for vendor procurement in a capital project.',
            'solution': 'Model Rubric:\n"Mandatory vendor verification of environmental disposal compliance for hazardous electronics, plus confirmation of fair wage certifications for all subcontracted labor prior to invoice approval."',
        },
    ],
    'cross-mentoring-in-project-teams': [
        {
            'order': 1,
            'title': 'Two-Way Mentoring: Bridging Senior Engineering with Digital PMOs',
            'synopsis': 'Pairing seasoned veteran managers with agile/digital practitioners to eliminate silos and preserve institutional memory.',
            'notes': (
                "1. Structured bidirectional mentoring frameworks.\n"
                "2. Reverse-mentoring: Digital tools, AI workflows, and agile cadences taught to senior leaders.\n"
                "3. Classic wisdom transfer: Stakeholder politics, negotiation, and contract instincts."
            ),
            'task': 'Design a 4-week paired mentoring sprint between a 20-year PM veteran and a digital Scrum Master.',
            'solution': 'Model Rubric:\nWeek 1: Cross-assessment of skill strengths.\nWeek 2: Digital Scrum Master demonstrates Jira/AI telemetry automation.\nWeek 3: Veteran PM coaches on executive negotiation and stakeholder handling.\nWeek 4: Co-author a joint project execution charter.',
        },
    ],
    'collaborating-in-projects': [
        {
            'order': 1,
            'title': 'Cross-Functional Interface Agreements & Handoff Maps',
            'synopsis': 'Eliminating departmental silos between engineering, procurement, legal, and operational units during deliverable handoffs.',
            'notes': (
                "1. Mapping interface points and handoff friction.\n"
                "2. Drafting Interface Agreements (IA): Input/output SLAs between departments.\n"
                "3. Joint dependency boards to align cross-team schedules."
            ),
            'task': 'Engineering blames Procurement for 3-week delays in component ordering. What Interface Agreement rule resolves this?',
            'solution': 'Model Rubric:\n"Engineering must deliver bill-of-materials with locked specs 14 days before procurement lead times. Procurement must issue RFQs within 48 hours of specification lock and provide real-time vendor tracking."',
        },
    ],
}

from datetime import date, timedelta
from courses.models import Course, Category, Cohort, CourseModule

def populate_modules():
    total_created = 0
    total_updated = 0

    # Ensure Corporate Training category exists
    corp_category, _ = Category.objects.get_or_create(
        slug='corporate-training',
        defaults={'name': 'Corporate Training', 'description': 'Executive capacity building and PM training.'}
    )

    # Human-readable titles mapping
    titles = {
        'leading-a-project-team': ('Leading a Project Team', 'fundamentals', 3, 15, 650),
        'working-adaptively': ('Working Adaptively', 'fundamentals', 3, 15, 650),
        'cross-mentoring-in-project-teams': ('Cross-Mentoring in Project Teams', 'fundamentals', 2, 12, 550),
        'starting-a-project': ('Starting a Project', 'fundamentals', 3, 15, 650),
        'planning-a-project': ('Planning a Project', 'fundamentals', 4, 20, 750),
        'executing-a-project': ('Executing a Project', 'fundamentals', 4, 20, 750),
        'closing-a-project': ('Closing a Project', 'fundamentals', 3, 15, 650),
        'building-an-empowered-team-culture': ('Building an Empowered Team Culture', 'intermediate', 3, 18, 750),
        'collaborating-in-projects': ('Collaborating in Projects', 'intermediate', 3, 18, 750),
        'engaging-project-stakeholders': ('Engaging Project Stakeholders', 'intermediate', 4, 20, 850),
        'managing-project-risk': ('Managing Project Risk', 'intermediate', 4, 24, 850),
        'project-performance-management': ('Project Performance Management', 'intermediate', 4, 24, 850),
        'project-metrics-and-reporting': ('Project Metrics and Reporting', 'intermediate', 3, 18, 750),
        'managing-project-knowledge': ('Managing Project Knowledge', 'intermediate', 3, 18, 750),
        'project-compliance-and-sustainability': ('Project Compliance and Sustainability', 'intermediate', 4, 20, 850),
    }

    for slug, modules_data in CURRICULUM_DATA.items():
        title_info = titles.get(slug, (slug.replace('-', ' ').title(), 'fundamentals', 3, 15, 650))

        # Auto-create the parent course if missing
        course, _ = Course.objects.get_or_create(
            slug=slug,
            defaults={
                'title': title_info[0],
                'category': corp_category,
                'level': title_info[1],
                'duration_weeks': title_info[2],
                'contact_hours': title_info[3],
                'fee': title_info[4],
                'tagline': f'Professional corporate mastery track for {title_info[0]}.',
                'overview': f'Rigorous industry curriculum delivering practical execution frameworks, templates, and field mechanics for {title_info[0]}.',
                'schedule_details': 'Saturdays: 9:00 AM – 2:00 PM GMT',
                'is_active': True,
            }
        )

        # Create active cohort if none exists
        if not course.cohorts.exists():
            Cohort.objects.create(
                course=course,
                cohort_code=f"Q4-{slug[:3].upper()}-26",
                start_date=date.today() + timedelta(days=14),
                end_date=date.today() + timedelta(days=14 + (title_info[2] * 7)),
                max_seats=25,
                is_open_for_enrollment=True
            )

        for mod_info in modules_data:
            module, created = CourseModule.objects.update_or_create(
                course=course,
                order=mod_info['order'],
                defaults={
                    'title': mod_info['title'],
                    'synopsis': mod_info['synopsis'],
                    'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'slide_deck_url': f'https://projectfocus.com/resources/slides/{slug}-mod{mod_info["order"]}.pptx',
                    'lecture_notes': mod_info['notes'],
                    'task_question': mod_info['task'],
                    'task_solution': mod_info['solution'],
                    'is_preview': (mod_info['order'] == 1),
                }
            )
            if created:
                total_created += 1
            else:
                total_updated += 1

    print(f"✓ Curriculum population complete: {total_created} modules created, {total_updated} modules updated across courses.")

if __name__ == '__main__':
    print("=" * 60)
    print("Project Focus • Modern PM Curriculum & Template Auto-Seeder")
    print("=" * 60)
    patch_allprograms_html()
    populate_modules()
    print("=" * 60)
    print("ALL DONE! Refresh http://127.0.0.1:8000/programs/ in your browser.")
    print("=" * 60)