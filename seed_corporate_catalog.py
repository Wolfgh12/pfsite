import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Category, Course, Cohort

def run_seed():
    print("--- Seeding Corporate Training Curriculum (3 per Tier) ---")

    # 1. Ensure Corporate Training category exists
    corporate_cat, _ = Category.objects.get_or_create(
        slug='corporate-training',
        defaults={
            'name': 'Corporate Project Management Training',
            'description': 'Tailored enterprise capacity development and execution tracks.'
        }
    )

    # 2. Reset existing corporate courses so we have a clean 3x3 lineup
    Course.objects.filter(category=corporate_cat).delete()

    curriculum = [
        # =====================================================================
        # TIER 1: FUNDAMENTALS
        # =====================================================================
        {
            "level": Course.Level.FUNDAMENTALS,
            "title": "Project Management Essentials & Chartering",
            "slug": "pm-essentials-chartering",
            "tagline": "Project Initiation, Stakeholder Alignment & Scope Definition",
            "overview": "Learn how to initiate corporate and engineering projects with absolute clarity. This course covers authoring binding project charters, identifying key enterprise stakeholders, establishing project governance boundaries, and defining initial assumptions and constraints.",
            "contact_hours": 24,
            "duration_weeks": 4,
            "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
            "schedule_details": "Saturdays: 9:00 AM – 3:00 PM GMT",
            "fee": 450.00,
            "deliverables": (
                "Approved Project Charter Master Template\n"
                "Stakeholder Register & Power-Interest Grid\n"
                "Project Scope Statement Blueprint\n"
                "24 PMI-Aligned Contact Hours Certificate"
            ),
        },
        {
            "level": Course.Level.FUNDAMENTALS,
            "title": "WBS Architecture & Task Effort Estimation",
            "slug": "wbs-architecture-task-estimation",
            "tagline": "Work Decomposition, 100% Rule & Scope Creep Prevention",
            "overview": "Master the art of breaking down complex capital works and corporate initiatives into manageable, accountable components. Focuses on the 100% decomposition rule, writing Work Package Dictionaries, and utilizing 3-point (PERT) estimating to prevent scope creep before field execution begins.",
            "contact_hours": 24,
            "duration_weeks": 4,
            "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
            "schedule_details": "Saturdays: 9:00 AM – 3:00 PM GMT",
            "fee": 480.00,
            "deliverables": (
                "Hierarchical Work Breakdown Structure (WBS) Model\n"
                "Work Package Dictionary & Scope Verification Checklist\n"
                "3-Point PERT Effort Estimation Spreadsheets\n"
                "24 PMI-Aligned Contact Hours Certificate"
            ),
        },
        {
            "level": Course.Level.FUNDAMENTALS,
            "title": "Basic Project Scheduling & Execution Coordination",
            "slug": "basic-scheduling-execution-coordination",
            "tagline": "Gantt Sequencing, RACI Frameworks & Daily Field Cadences",
            "overview": "A hands-on execution workshop for site engineers and coordinators. Learn to construct clear Gantt schedules using logical predecessors, establish accountable RACI matrices across internal teams and vendors, and manage structured daily stand-ups and progress logs.",
            "contact_hours": 24,
            "duration_weeks": 4,
            "delivery_mode": Course.DeliveryMode.HYBRID,
            "schedule_details": "Saturdays: 10:00 AM – 4:00 PM GMT",
            "fee": 450.00,
            "deliverables": (
                "Production Gantt Baseline Schedule Template\n"
                "Enterprise RACI Accountability Matrix\n"
                "Field Progress Reporting & Action Item Log\n"
                "24 PMI-Aligned Contact Hours Certificate"
            ),
        },

        # =====================================================================
        # TIER 2: INTERMEDIATE
        # =====================================================================
        {
            "level": Course.Level.INTERMEDIATE,
            "title": "Critical Path Method (CPM) & Schedule Dynamics",
            "slug": "cpm-schedule-dynamics-control",
            "tagline": "Network Logic, Float Optimization & Schedule Compression",
            "overview": "Deep-dive into rigorous mathematical schedule analysis. Learn Forward and Backward pass calculations, identify Critical Path dependency chains, manage Total vs. Free Float, and evaluate crashing versus fast-tracking strategies to recover slipping baselines.",
            "contact_hours": 35,
            "duration_weeks": 6,
            "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
            "schedule_details": "Saturdays: 9:00 AM – 4:00 PM GMT",
            "fee": 650.00,
            "deliverables": (
                "CPM Precedence Diagramming Analysis Workbook\n"
                "Schedule Compression & Float Management Framework\n"
                "Milestone Trend & Slip-Curve Tracking Models\n"
                "35 PMI-Aligned Contact Hours Certificate"
            ),
        },
        {
            "level": Course.Level.INTERMEDIATE,
            "title": "Earned Value Management (EVM) & Cost Integrity",
            "slug": "evm-cost-integrity-control",
            "tagline": "Quantitative Performance Control, Cost Variance & EAC Forecasting",
            "overview": "Bridge finance and engineering through rigorous EVM controls. Learn to track Cost Variance (CV) and Schedule Variance (SV) against verified physical progress rather than contractor payment requests. Master CPI, SPI, and Estimate at Completion (EAC) projections for senior management.",
            "contact_hours": 35,
            "duration_weeks": 6,
            "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
            "schedule_details": "Saturdays: 9:00 AM – 4:00 PM GMT",
            "fee": 700.00,
            "deliverables": (
                "Enterprise EVM Financial Dashboard (CPI/SPI/EAC)\n"
                "Physical Progress vs. Financial Drawdown Auditor\n"
                "Monthly Steering Committee Cost Report Package\n"
                "35 PMI-Aligned Contact Hours Certificate"
            ),
        },
        {
            "level": Course.Level.INTERMEDIATE,
            "title": "Contractor Oversight & Procurement Management",
            "slug": "contractor-oversight-procurement",
            "tagline": "Subcontractor Evaluation, Milestone Audits & SLA Enforcement",
            "overview": "Designed for project managers overseeing outsourced vendors and main contractors. Covers crafting unambiguous Statements of Work (SOW), executing objective contractor evaluation scoring, verifying milestone delivery sign-offs, and resolving on-site discrepancies before invoices are released.",
            "contact_hours": 30,
            "duration_weeks": 5,
            "delivery_mode": Course.DeliveryMode.HYBRID,
            "schedule_details": "Saturdays: 9:00 AM – 3:30 PM GMT",
            "fee": 620.00,
            "deliverables": (
                "Contractor Performance & SLA Audit Scorecard\n"
                "Milestone Inspection & Handover Sign-Off Protocols\n"
                "Subcontractor Variance & Non-Conformance Log\n"
                "30 PMI-Aligned Contact Hours Certificate"
            ),
        },

        # =====================================================================
        # TIER 3: ADVANCED
        # =====================================================================
        {
            "level": Course.Level.ADVANCED,
            "title": "FIDIC Contract Administration & Claims Management",
            "slug": "fidic-contract-admin-claims",
            "tagline": "Red & Yellow Book Protocols, Clause 20 Claims & Dispute Boards",
            "overview": "Master high-stakes contract administration under international FIDIC standards (Red, Yellow, and Silver books). Focuses on employer and contractor rights, the Engineer's role, navigating Clause 20 notice periods, claim defense, and Dispute Adjudication Board (DAB) procedures.",
            "contact_hours": 40,
            "duration_weeks": 8,
            "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
            "schedule_details": "Saturdays: 9:00 AM – 4:30 PM GMT",
            "fee": 950.00,
            "deliverables": (
                "FIDIC Clause-by-Clause Contract Admin Manual\n"
                "Contractor Notice of Claim Assessment Matrix\n"
                "Dispute Adjudication Board (DAB) Hearing Case Studies\n"
                "40 Accredited CPD / PDU Contact Hours"
            ),
        },
        {
            "level": Course.Level.ADVANCED,
            "title": "Forensic Delay Analysis & Liquidated Damages Recovery",
            "slug": "forensic-delay-analysis-recovery",
            "tagline": "As-Planned vs. As-Built, Time Impact Analysis & Concurrency",
            "overview": "An advanced masterclass in forensic critical path delay analysis. Learn to reconstruct delays using As-Planned vs As-Built, Collapsed As-Built, and Time Impact Analysis (TIA). Identify concurrent delays, assess excusable compensable events, and substantiate or defend claims for liquidated damages.",
            "contact_hours": 40,
            "duration_weeks": 8,
            "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
            "schedule_details": "Saturdays: 9:00 AM – 4:30 PM GMT",
            "fee": 980.00,
            "deliverables": (
                "Forensic Time Impact Analysis (TIA) Model\n"
                "Concurrent Delay Assessment Protocols\n"
                "Liquidated Damages Legal Defense Dossier\n"
                "40 Accredited CPD / PDU Contact Hours"
            ),
        },
        {
            "level": Course.Level.ADVANCED,
            "title": "Enterprise PMO Setup & Capital Stage-Gate Governance",
            "slug": "enterprise-pmo-stage-gate-governance",
            "tagline": "Portfolio Prioritization, Stage-Gate Controls & Board Oversight",
            "overview": "A strategic framework for PMO directors and enterprise executives. Learn to build and scale a value-driven Corporate PMO, design mandatory Stage-Gate review gates (feasibility, procurement, execution, handover), and provide data-driven project portfolio reporting for executive boards.",
            "contact_hours": 35,
            "duration_weeks": 6,
            "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
            "schedule_details": "Saturdays: 9:00 AM – 3:30 PM GMT",
            "fee": 900.00,
            "deliverables": (
                "Complete Enterprise PMO Charter & Operational Manual\n"
                "Capital Stage-Gate Review Governance Framework\n"
                "Executive Steering Committee Board Pack Templates\n"
                "35 Accredited CPD / PDU Contact Hours"
            ),
        },
    ]

    base_start = date(2026, 11, 7)

    for item in curriculum:
        course = Course.objects.create(
            category=corporate_cat,
            level=item["level"],
            title=item["title"],
            slug=item["slug"],
            tagline=item["tagline"],
            overview=item["overview"],
            contact_hours=item["contact_hours"],
            duration_weeks=item["duration_weeks"],
            delivery_mode=item["delivery_mode"],
            schedule_details=item["schedule_details"],
            deliverables=item["deliverables"],
            fee=item["fee"],
            is_active=True
        )

        # Create upcoming cohort
        Cohort.objects.create(
            course=course,
            cohort_code=f"CORP-{course.slug[:4].upper()}-NOV26",
            start_date=base_start,
            end_date=base_start + timedelta(weeks=course.duration_weeks),
            max_seats=20,
            is_open_for_enrollment=True
        )

    print("Success: Seeded 9 Corporate Training courses (3 Fundamentals, 3 Intermediate, 3 Advanced) with active cohorts.")

if __name__ == '__main__':
    run_seed()