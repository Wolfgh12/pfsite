import os
import re
import django
from datetime import date

# Auto-detect your project's settings module from manage.py
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    with open('manage.py', 'r', encoding='utf-8') as f:
        match = re.search(r"DJANGO_SETTINGS_MODULE['\"],\s*['\"]([^'\"]+)['\"]", f.read())
        if match:
            os.environ['DJANGO_SETTINGS_MODULE'] = match.group(1)

django.setup()

from courses.models import Category, Course, Cohort

print("Starting Project Focus catalog seed...")

# 1. Categories
cat_corp, _ = Category.objects.get_or_create(
    slug='corporate-training',
    defaults={
        'name': 'Corporate Project Management Training',
        'description': 'Applied corporate curricula designed for commercial teams, engineers, and enterprise leaders.'
    }
)

cat_cert, _ = Category.objects.get_or_create(
    slug='certifications',
    defaults={
        'name': 'Project Management Certification',
        'description': 'Internationally accredited PMI® credential preparation programs.'
    }
)

cat_consult, _ = Category.objects.get_or_create(
    slug='consulting',
    defaults={
        'name': 'Project Management Consulting',
        'description': 'Directorate advisory services, forensic project auditing, and PMO governance setups.'
    }
)

# 2. Syllabi & Catalog Offerings
catalog = [
    # Corporate Training
    {
        'category': cat_corp,
        'title': 'Corporate PM: Fundamentals Course',
        'slug': 'fundamentals-course',
        'tagline': 'Applied Project Foundations • PMBOK® 7th Edition & Agile Mindset',
        'overview': 'Designed for cross-functional teams, emerging coordinators, and operational supervisors transitioning into capital works. Master project life cycles, charter formulation, stakeholder analysis, and baseline scope planning under PMBOK 7th Edition principles.',
        'contact_hours': 21,
        'duration_weeks': 4,
        'delivery_mode': Course.DeliveryMode.WEEKEND_INTENSIVE,
        'schedule_details': 'Saturdays: 9:00 AM – 3:00 PM GMT',
        'deliverables': "21 PMI-Approved Contact Hours\nProject Charter & Governance Framework\nWork Breakdown Structure (WBS) Templates\nStakeholder Engagement Grid\nProject Focus Certification of Completion",
        'fee': 650.00,
        'is_featured': True,
    },
    {
        'category': cat_corp,
        'title': 'Corporate PM: Intermediate Course',
        'slug': 'intermediate-course',
        'tagline': 'Applied Project Execution, Earned Value & Schedule Defense',
        'overview': 'Engineered for practicing project managers and supervisors tasked with keeping capital projects on time and within budget. Focuses on Critical Path Method (CPM) calculation, 100% WBS baselines, variance tracking, and Earned Value Management (EVM).',
        'contact_hours': 30,
        'duration_weeks': 6,
        'delivery_mode': Course.DeliveryMode.WEEKEND_INTENSIVE,
        'schedule_details': 'Saturdays: 9:00 AM – 4:00 PM GMT',
        'deliverables': "30 PMI-Approved Contact Hours\nCritical Path Method (CPM) Schedule Calculation Models\nEarned Value Management (EVM) Financial S-Curves\nQualitative Risk Register Matrix\nBaseline Change Control Board (CCB) Procedures",
        'fee': 950.00,
        'is_featured': True,
    },
    {
        'category': cat_corp,
        'title': 'Corporate PM: Advanced Courses',
        'slug': 'advanced-courses',
        'tagline': 'Megaproject Governance, EPC Contracting & Boardroom Leadership',
        'overview': 'Executive delivery designed for project directors, commercial heads, and engineering leads managing capital investments. Master Stage-Gate approval governance, contractor claim defense, FIDIC/EPC contracts, and executive steering committee defense.',
        'contact_hours': 40,
        'duration_weeks': 8,
        'delivery_mode': Course.DeliveryMode.HYBRID,
        'schedule_details': 'Fridays: 5:00 PM – 8:00 PM | Saturdays: 9:00 AM – 2:00 PM GMT',
        'deliverables': "40 Accredited Executive PDUs\nFIDIC & EPC Infrastructure Claim Defense Frameworks\nStage-Gate Boardroom Approval Governance Model\nForensic Delay Claim Analysis Documentation\nExecutive Director Capstone Assessment",
        'fee': 1500.00,
        'is_featured': True,
    },

    # PMI Certifications
    {
        'category': cat_cert,
        'title': 'Certified Associate in Project Management (CAPM)®',
        'slug': 'capm-certification-prep',
        'tagline': 'Official 23 PMI Contact Hours • Predictive, Adaptive & Business Analysis',
        'overview': 'Comprehensive certification boot camp designed for entry-to-mid career professionals preparing for PMI’s CAPM® examination. Rigorous coverage of predictive PMBOK frameworks, agile execution, and business analysis fundamentals.',
        'contact_hours': 23,
        'duration_weeks': 5,
        'delivery_mode': Course.DeliveryMode.ONLINE_LIVE,
        'schedule_details': 'Tuesdays & Thursdays: 6:00 PM – 8:30 PM GMT',
        'deliverables': "23 PMI-Approved Contact Hours (Full Exam Eligibility)\nComplete CAPM Exam Simulator Access (1,000+ Questions)\nPredictive & Adaptive Process Mappings\nPMI Examination Application Walkthrough\nDirectorate Study Diagnostic Review",
        'fee': 750.00,
        'is_featured': False,
    },
    {
        'category': cat_cert,
        'title': 'Project Management Professional (PMP)® Exam Mastery',
        'slug': 'pmp-exam-mastery',
        'tagline': '35 Accredited PMI Contact Hours • People, Process & Business Environment',
        'overview': 'The gold-standard certification course for experienced project leaders. Complete mastery across the 3 PMP domains—People, Process, and Business Environment—spanning predictive, hybrid, and agile methodologies.',
        'contact_hours': 35,
        'duration_weeks': 8,
        'delivery_mode': Course.DeliveryMode.WEEKEND_INTENSIVE,
        'schedule_details': 'Saturdays: 9:00 AM – 3:30 PM GMT',
        'deliverables': "35 PMI-Approved Contact Hours (Mandatory Exam Requirement)\nPMP Diagnostic Exam Simulation Bank (2,000+ Scenario Questions)\nFull Agile Practice Guide & PMBOK 7th Ed. Synthesis\n1-on-1 PMI Application Review & Audit Guarantee\nDirect Advisory Mentorship with Director awuah",
        'fee': 1200.00,
        'is_featured': True,
    },
    {
        'category': cat_cert,
        'title': 'Risk Management Professional (PMI-RMP)® Track',
        'slug': 'rmp-certification-prep',
        'tagline': 'Quantitative Risk Modeling, Monte Carlo Concepts & Threat Defense',
        'overview': 'Specialized credential track for capital project risk managers, estimators, and controllers. Master qualitative and quantitative risk analysis, risk response strategies, contingency reserve formulas, and Monte Carlo probability modeling.',
        'contact_hours': 30,
        'duration_weeks': 6,
        'delivery_mode': Course.DeliveryMode.HYBRID,
        'schedule_details': 'Saturdays: 10:00 AM – 3:00 PM GMT',
        'deliverables': "30 PMI-Approved Contact Hours\nQuantitative Risk Assessment (QRA) Spreadsheets\nMonte Carlo Probability Schedule & Cost Simulations\nThreat & Opportunity Matrix Integration\nOfficial PMI-RMP Mock Examination Suite",
        'fee': 1100.00,
        'is_featured': False,
    },
    {
        'category': cat_cert,
        'title': 'Scheduling Management Professional (SMP / PMI-SP)® Track',
        'slug': 'smp-scheduling-management',
        'tagline': 'Advanced Primavera P6 Logic, Baseline Float Defense & Earned Schedule',
        'overview': 'Tailored for senior planners, scheduling engineers, and project controllers. Covers network diagram logic, total and free float defense, schedule compression, and forensic delay analysis.',
        'contact_hours': 30,
        'duration_weeks': 6,
        'delivery_mode': Course.DeliveryMode.HYBRID,
        'schedule_details': 'Saturdays: 9:00 AM – 2:00 PM GMT',
        'deliverables': "30 PMI-Approved Contact Hours\nPrimavera P6 & MS Project Advanced Logic Templates\nCritical Path Schedule Float & Crashing Models\nEarned Schedule (ES) vs Earned Value Calculations\nOfficial PMI-SP Examination Preparation Pack",
        'fee': 1100.00,
        'is_featured': False,
    },

    # Consulting Services
    {
        'category': cat_consult,
        'title': 'Project Governance Assistance',
        'slug': 'project-governance-assistance',
        'tagline': 'Boardroom PMO Setup, Stage-Gate Frameworks & Executive Charters',
        'overview': 'Specialized institutional advisory service for corporate boards, developers, and public sector ministries. Project Focus establishes robust Project Management Offices (PMO), Stage-Gate approval thresholds, and change control governance structures.',
        'contact_hours': 40,
        'duration_weeks': 12,
        'delivery_mode': Course.DeliveryMode.HYBRID,
        'schedule_details': 'Corporate Advisory Delivery • Tailored Schedule',
        'deliverables': "Institutional PMO Charter & Mandate\nEnterprise Stage-Gate Governance Matrix\nCapital Expenditure Approval Threshold Protocols\nExecutive Board Reporting Dashboards",
        'fee': 0.00,
        'is_featured': False,
    },
    {
        'category': cat_consult,
        'title': 'Technical Project Auditing',
        'slug': 'technical-project-auditing',
        'tagline': 'Forensic Schedule Analysis, Cost Verification & Delay Claim Audits',
        'overview': 'Independent third-party technical investigation into capital works experiencing delays, budget runaways, or contractor disputes. Provides lenders, owners, and directors with unvarnished empirical findings.',
        'contact_hours': 35,
        'duration_weeks': 4,
        'delivery_mode': Course.DeliveryMode.HYBRID,
        'schedule_details': 'On-Site Field Investigation & Remote Audit',
        'deliverables': "Forensic Schedule Delay Analysis Report\nEarned Value Cost Verification Audit\nContractor Variation & Claim Merit Assessment\nTurnaround Remediation Roadmap",
        'fee': 0.00,
        'is_featured': False,
    },
    {
        'category': cat_consult,
        'title': 'Project Management Advice',
        'slug': 'project-management-advice',
        'tagline': 'Strategic Retainer Advisory Directly with Director awuah',
        'overview': 'Direct confidential advisory retained by project sponsors, executive boards, and managing directors. Receive high-level guidance on procurement strategy, contractor negotiations, risk exposure, and troubled project recovery.',
        'contact_hours': 20,
        'duration_weeks': 8,
        'delivery_mode': Course.DeliveryMode.HYBRID,
        'schedule_details': 'Executive Retainer Sessions',
        'deliverables': "Direct Strategic Counsel with Director awuah\nProcurement & FIDIC Contracting Strategy Reviews\nHigh-Stakes Stakeholder Alignment Sessions\nIndependent Project Health Diagnostics",
        'fee': 0.00,
        'is_featured': False,
    },
]

# 3. Wipe legacy courses, scrum tracks, and categories not in the official catalog
valid_slugs = [item['slug'] for item in catalog]
valid_cat_slugs = ['corporate-training', 'certifications', 'consulting']

from courses.models import Registration

legacy_courses = Course.objects.exclude(slug__in=valid_slugs)
Registration.objects.filter(cohort__course__in=legacy_courses).delete()
Cohort.objects.filter(course__in=legacy_courses).delete()
legacy_courses.delete()
Category.objects.exclude(slug__in=valid_cat_slugs).delete()
print("✓ Purged all legacy courses, scrum tracks, and outdated categories.")

# 4. Create or update records & cohorts
for item in catalog:
    course, created = Course.objects.update_or_create(
        slug=item['slug'],
        defaults=item
    )
    action = "Created" if created else "Updated"
    print(f"[{action}] Course: {course.title}")

    if course.category != cat_consult:
        cohorts = [
            {'code': f"{course.slug[:3].upper()}-NOV-2026", 'start': date(2026, 11, 7), 'end': date(2026, 12, 19), 'seats': 25},
            {'code': f"{course.slug[:3].upper()}-JAN-2027", 'start': date(2027, 1, 16), 'end': date(2027, 3, 6), 'seats': 25},
            {'code': f"{course.slug[:3].upper()}-APR-2027", 'start': date(2027, 4, 10), 'end': date(2027, 5, 29), 'seats': 25},
        ]
        for c in cohorts:
            Cohort.objects.get_or_create(
                course=course,
                cohort_code=c['code'],
                defaults={
                    'start_date': c['start'],
                    'end_date': c['end'],
                    'max_seats': c['seats'],
                    'is_open_for_enrollment': True,
                }
            )

print("Catalog seeding complete.")