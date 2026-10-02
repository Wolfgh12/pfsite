from datetime import date, timedelta
from django.core.management.base import BaseCommand
from courses.models import Category, Course, Cohort


class Command(BaseCommand):
    help = "Seeds clear, real-world project management courses and upcoming cohorts."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Resetting course database with fresh data..."))

        Cohort.objects.all().delete()
        Course.objects.all().delete()
        Category.objects.all().delete()

        # 1. Categories
        cat_pmp = Category.objects.create(
            name="PMP & Certifications",
            description="Preparatory cohorts for international certifications including PMP, CAPM, and foundational credentials."
        )
        cat_agile = Category.objects.create(
            name="Agile & Tech Delivery",
            description="Practical training for software teams, product managers, and agile coordinators."
        )
        cat_infra = Category.objects.create(
            name="Construction & Site Works",
            description="Field management, contractor supervision, safety, and contract administration for physical projects."
        )
        cat_finance = Category.objects.create(
            name="Cost & Budget Control",
            description="Financial tracking, invoice reviews, variance forecasting, and project cash flow management."
        )

        self.stdout.write(self.style.SUCCESS(f"Created {Category.objects.count()} categories."))

        # 2. Courses with plain, professional copy
        courses_data = [
            # PMP Track
            {
                "category": cat_pmp,
                "title": "PMP® Exam Prep & Practical Delivery",
                "tagline": "Pass your exam on the first attempt and run projects with confidence.",
                "overview": (
                    "We walk you through everything needed to pass the PMP exam without memorizing "
                    "useless trivia. More importantly, we connect every concept to daily job realities: "
                    "how to build realistic schedules, manage difficult stakeholders, and keep your "
                    "project from falling behind."
                ),
                "contact_hours": 35,
                "duration_weeks": 8,
                "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
                "schedule_details": "Saturdays: 9:00 AM – 2:00 PM GMT",
                "deliverables": (
                    "35 official contact hours certificate required for PMI application\n"
                    "One-on-one review of your application experience before submission\n"
                    "Full access to 1,000+ realistic practice exam questions\n"
                    "Ready-to-use project charter and stakeholder register templates"
                ),
                "fee": 4500.00,
                "is_featured": True,
                "cohort_code": "PMP-OCT-2026",
                "start_offset_weeks": 3,
                "seats": 25,
            },
            {
                "category": cat_pmp,
                "title": "Project Management Fundamentals (CAPM®)",
                "tagline": "A structured foundation for early-career managers and coordinators.",
                "overview": (
                    "Designed for team leads, coordinators, and recent graduates who want to run projects "
                    "systematically. You will learn the core lifecycle of a project—from initial scoping "
                    "and task assignment to risk tracking and final project closeout."
                ),
                "contact_hours": 23,
                "duration_weeks": 5,
                "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
                "schedule_details": "Saturdays: 9:00 AM – 1:30 PM GMT",
                "deliverables": (
                    "23 PMI-approved contact hours certificate\n"
                    "Step-by-step guidance for writing clear work breakdown structures\n"
                    "Introductory risk log and issue tracking spreadsheets\n"
                    "CAPM exam practice questions and test-taking strategy guide"
                ),
                "fee": 2600.00,
                "is_featured": False,
                "cohort_code": "CAPM-NOV-2026",
                "start_offset_weeks": 6,
                "seats": 20,
            },

            # Agile Track
            {
                "category": cat_agile,
                "title": "Agile Delivery & Scrum Master Training",
                "tagline": "Run focused sprints and keep your team delivering on time.",
                "overview": (
                    "Many teams adopt Agile on paper but still struggle with chaotic backlogs and missed deadlines. "
                    "This course shows you how Scrum works when applied properly. You will learn how to estimate "
                    "effort accurately, run 15-minute standups that stay on point, and handle shifting client priorities."
                ),
                "contact_hours": 24,
                "duration_weeks": 4,
                "delivery_mode": Course.DeliveryMode.EVENING_TRACK,
                "schedule_details": "Tues & Thurs: 6:30 PM – 9:00 PM GMT",
                "deliverables": (
                    "Full preparation for PSM I / CSM certification exams\n"
                    "Hands-on board configuration in Jira and Trello\n"
                    "Sprint planning, daily scrum, and retrospective facilitation guides\n"
                    "Practical techniques for managing scope changes without team burnout"
                ),
                "fee": 3200.00,
                "is_featured": True,
                "cohort_code": "SCRUM-OCT-2026",
                "start_offset_weeks": 4,
                "seats": 20,
            },

            # Infrastructure / Site Track
            {
                "category": cat_infra,
                "title": "Site Management & Contractor Supervision",
                "tagline": "Keep physical builds on schedule, verify work quality, and handle claims.",
                "overview": (
                    "Tailored for site engineers, quantity surveyors, and project directors overseeing physical "
                    "works. Learn how to track progress on site, document daily occurrences to prevent dispute claims, "
                    "manage sub-contractor delays, and navigate standard contract conditions."
                ),
                "contact_hours": 30,
                "duration_weeks": 6,
                "delivery_mode": Course.DeliveryMode.WEEKEND_INTENSIVE,
                "schedule_details": "Saturdays: 10:00 AM – 2:30 PM GMT",
                "deliverables": (
                    "Plain-English guide to FIDIC conditions and contractor notices\n"
                    "Standard daily site diary and milestone tracking templates\n"
                    "Clear procedures for handling delay notifications and variations\n"
                    "Taking-Over and defect liability inspection checklists"
                ),
                "fee": 4800.00,
                "is_featured": True,
                "cohort_code": "SITE-OCT-2026",
                "start_offset_weeks": 4,
                "seats": 18,
            },

            # Cost Control Track
            {
                "category": cat_finance,
                "title": "Project Cost Engineering & Budget Control",
                "tagline": "Catch budget overruns early and forecast final costs with accuracy.",
                "overview": (
                    "Most project budgets fail quietly before anyone realizes there is a problem. In this workshop, "
                    "you will learn how to build solid cost baselines, track true labor and materials spending against "
                    "actual progress, and present clean financial reports to executive leaders."
                ),
                "contact_hours": 18,
                "duration_weeks": 3,
                "delivery_mode": Course.DeliveryMode.ONLINE_LIVE,
                "schedule_details": "Fridays: 5:30 PM – 8:30 PM GMT",
                "deliverables": (
                    "Excel cost tracking template with automated variance formulas\n"
                    "Step-by-step Earned Value calculations made simple\n"
                    "Checklists for evaluating contractor payment certificates\n"
                    "Executive monthly cost report format ready for board presentation"
                ),
                "fee": 2800.00,
                "is_featured": False,
                "cohort_code": "COST-NOV-2026",
                "start_offset_weeks": 5,
                "seats": 20,
            },
        ]

        # 3. Create Courses and Cohorts
        today = date(2026, 9, 25)

        for cdata in courses_data:
            course = Course.objects.create(
                category=cdata["category"],
                title=cdata["title"],
                tagline=cdata["tagline"],
                overview=cdata["overview"],
                contact_hours=cdata["contact_hours"],
                duration_weeks=cdata["duration_weeks"],
                delivery_mode=cdata["delivery_mode"],
                schedule_details=cdata["schedule_details"],
                deliverables=cdata["deliverables"],
                fee=cdata["fee"],
                is_featured=cdata["is_featured"],
                is_active=True,
            )

            start = today + timedelta(weeks=cdata["start_offset_weeks"])
            end = start + timedelta(weeks=cdata["duration_weeks"])

            Cohort.objects.create(
                course=course,
                cohort_code=cdata["cohort_code"],
                start_date=start,
                end_date=end,
                max_seats=cdata["seats"],
                is_open_for_enrollment=True,
            )

        self.stdout.write(self.style.SUCCESS(f"Created {Course.objects.count()} active courses."))
        self.stdout.write(self.style.SUCCESS(f"Created {Cohort.objects.count()} scheduled cohorts."))
        self.stdout.write(self.style.SUCCESS("Database seeded successfully with clean, professional copy!"))