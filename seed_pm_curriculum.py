import os
import re
from pathlib import Path
from datetime import date, timedelta
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Course, Category, Cohort, CourseModule

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
        title_pattern = rf'<h2 class="text-xl font-bold text-white mb-2 leading-snug">\s*{re.escape(title)}\s*</h2>'
        replacement_title = (
            f'<h2 class="text-xl font-bold text-white mb-2 leading-snug">\n'
            f'          <a href="{{% url \'courses:detail\' \'{slug}\' %}}" class="hover:text-sea-cyan transition-colors">\n'
            f'            {title}\n'
            f'          </a>\n'
            f'        </h2>'
        )
        content = re.sub(title_pattern, replacement_title, content)

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
    print("✓ Successfully updated course titles and buttons in templates/allprograms.html")


# -----------------------------------------------------------------------------
# 2. PMBOK® 8TH EDITION AUTHENTIC CURRICULUM DATASET
# -----------------------------------------------------------------------------
CURRICULUM_DATA = {
    'leading-a-project-team': [
        {
            'order': 1,
            'title': 'High-Trust Working Agreements, Systems Thinking & Psychological Safety',
            'synopsis': 'PMBOK 8th Edition collaborative team leadership, psychological safety metrics, and self-organizing team architectures.',
            'notes': (
                "1. PMBOK 8th Edition Team Stewardship: Transitioning from command-and-control to servant systems facilitation.\n"
                "2. Amy Edmondson's Psychological Safety Architecture: Decoupling error disclosure from career repercussions in mission-critical environments.\n"
                "3. Social Operating Contracts: Defining core synchronous hours, asynchronous decision latency, and transparent issue escalation paths."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A multidisciplinary delivery unit (EPC engineering leads and cloud telemetry software developers) is experiencing acute friction. "
                "Engineering accuses software developers of deploying unverified schema migrations that disrupt industrial sensors. "
                "Developers claim civil engineering stage-gates create 3-week idle bottlenecks.\n\n"
                "Candidate Assignment:\n"
                "1. Draft a 4-point Team Operating Agreement resolving cross-functional deployment friction.\n"
                "2. Define the exact psychological safety mechanism allowing technicians to halt work upon sensing an anomaly without penalty.\n"
                "3. Specify the metrics used to track team trust over consecutive release cycles."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Team Operating Agreement (40 Marks):\n"
                "• Explicit Definition of Ready (DoR) and Done (DoD) bridging software and EPC hardware interfaces.\n"
                "• Core synchronous alignment window (10:00 AM – 2:00 PM GMT); all other communications strictly asynchronous with a 4-hour SLA.\n"
                "• Joint deployment review sessions scheduled 48 hours prior to sensor network integration.\n"
                "• Clear Escalation Protocol: Disagreements lasting over 2 hours escalate directly to the Project Delivery Lead for mediation.\n\n"
                "2. Anomaly Disclosure Safeguard (30 Marks):\n"
                "Implement an Andon-cord protocol empowering any technician to freeze a staging release immediately upon detecting safety or telemetry anomalies. Management explicitly conducts blameless systems reviews to investigate pipeline defects.\n\n"
                "3. Trust Telemetry Metrics (30 Marks):\n"
                "Track Anonymous Safety Index scores during bi-weekly retrospectives, Mean Time to Acknowledge (MTTA) blockers, and the ratio of internally self-corrected defects vs. client-discovered defects."
            ),
        },
        {
            'order': 2,
            'title': 'Situational Leadership, Adaptive Conflict De-escalation & Emotional Intelligence',
            'synopsis': 'Applying Hersey-Blanchard situational leadership to elite technical talent and de-escalating architectural friction.',
            'notes': (
                "1. PMBOK 8th Edition Adaptive Leadership: Fluid calibration between Directing, Coaching, Supporting, and Delegating.\n"
                "2. Interest-Based Relational (IBR) Strategy: Separating personal identity from structural project constraints.\n"
                "3. Managing Specialized Dissent: Channeling technical pushback into baseline refinement without compromising project milestones."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A Principal Data Architect with specialized domain expertise refuses to comply with PMO documentation standards, "
                "bypassing code peer-reviews and deploying proprietary microservices directly to production. "
                "When challenged during a standup, the architect threatens to resign 4 weeks before commercial launch.\n\n"
                "Candidate Assignment:\n"
                "1. Diagnose the architect's situational maturity quadrant and detail your leadership stance adjustment.\n"
                "2. Formulate your 1-on-1 private de-escalation discussion strategy.\n"
                "3. Establish a defensible governance compromise that secures documentation compliance without losing the architect."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Situational Diagnosis (30 Marks):\n"
                "The architect demonstrates high technical competence but low organizational/governance commitment (D3/Supporting quadrant). Immediate Directing posture will trigger resignation; transition to a Supporting/Coaching posture focused on mutual objectives.\n\n"
                "2. Private Intervention Strategy (35 Marks):\n"
                "Conduct a private alignment session utilizing the IBR method. Validate their technical brilliance while presenting the business operational risk of single-point-of-failure vulnerabilities. Frame compliance not as bureaucratic control, but as architectural resilience.\n\n"
                "3. Governance Compromise (35 Marks):\n"
                "Assign a junior systems engineer to pair-shadow the architect and author the formal Architecture Decision Records (ADRs) and OpenAPI schemas directly from the architect's designs, preserving the architect's focus while securing full PMO baseline compliance."
            ),
        },
    ],
    'working-adaptively': [
        {
            'order': 1,
            'title': 'Hybrid Delivery Governance: Blending Predictive Stage-Gates with Agile Flow',
            'synopsis': 'Harmonizing PMBOK 8th Edition stage-gate oversight with iterative value-stream sprints, WIP limits, and rapid feedback loops.',
            'notes': (
                "1. Cynefin Complexity Framework: Discerning Complex versus Complicated delivery domains to select delivery lifecycles.\n"
                "2. Hybrid Governance Gates: Predictive capital budgeting combined with rolling-wave adaptive sprint increments.\n"
                "3. Little's Law & Flow Telemetry: Managing Work-In-Progress (WIP) to prevent delivery pipeline thrashing."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A national railway authority is commissioning a digital signaling and ticketing modernization project. "
                "The Ministry of Finance mandates fixed predictive stage-gate reviews every 60 days to unlock tranche financing. "
                "However, commuter experience modules require bi-weekly iterative user-testing and agile releases.\n\n"
                "Candidate Assignment:\n"
                "1. Architect the hybrid delivery framework that satisfies both the Ministry's 60-day audit gates and bi-weekly sprint cadences.\n"
                "2. Detail how sprint review artifacts map into the formal Stage-Gate Deliverable Dossier.\n"
                "3. Define the threshold where an agile scope pivot triggers a formal Integrated Change Control (ICC) review."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Hybrid Delivery Architecture (35 Marks):\n"
                "Structure the overarching program using predictive Stage-Gates for statutory compliance, civil signaling safety, and tranche disbursements. Nest four 2-week adaptive sprints within each 60-day funding gate cycle to iterate user-facing software and interfaces.\n\n"
                "2. Deliverable Dossier Mapping (35 Marks):\n"
                "Aggregate completed sprint increments into an executive 'Value Delivery Increment' package. Demonstrate cumulative flow burnup, automated test coverage reports, and stakeholder acceptance sign-offs as the primary evidence for the Ministry's stage-gate release.\n\n"
                "3. Governance Variance Threshold (30 Marks):\n"
                "Sprint backlog reprioritization remains entirely within the Product Owner's authority provided it does not alter statutory compliance, compromise civil safety criteria, or exceed +/- 5% of the gate's financial allocation. Any breach immediately triggers formal ICC review."
            ),
        },
        {
            'order': 2,
            'title': 'AI-Augmented Sprint Cadences, Flow Telemetry & Backlog Dynamic Value Prioritization',
            'synopsis': 'Executing high-velocity sprint ceremonies, eliminating story point inflation, and utilizing AI-driven value forecasting.',
            'notes': (
                "1. Weighted Shortest Job First (WSJF) & Cost of Delay (CoD) mathematical modeling for backlog optimization.\n"
                "2. Eliminating Velocity Inflation: Replacing vanity velocity with Throughput and Cycle-Time telemetry.\n"
                "3. Predictive Retrospectives: Converting retrospective telemetry into automated continuous integration safeguards."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "Over three consecutive sprints, a delivery team's committed story points rose from 60 to 95, yet the actual business value "
                "delivered to operations declined by 40% due to technical rework and story point inflation. "
                "The project sponsor questions team integrity.\n\n"
                "Candidate Assignment:\n"
                "1. Perform root cause diagnostics on the story point inflation phenomenon.\n"
                "2. Recalibrate the team's performance metrics using PMBOK 8th Edition flow telemetry (Cycle Time vs Throughput).\n"
                "3. Draft the sponsor briefing transparently clarifying the real delivery velocity."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Root Cause Diagnostics (30 Marks):\n"
                "Story point inflation occurred because the team decomposed large complex tasks into superficial sub-stories to hit artificial velocity targets, while defect remediation and technical debt went unestimated, consuming real productive capacity.\n\n"
                "2. Metric Recalibration (35 Marks):\n"
                "De-emphasize story points. Institute Little's Law flow telemetry: Measure Work-In-Progress (WIP), Cycle Time (days from 'In Progress' to 'Done'), and Weekly Feature Throughput. Calibrate backlog prioritization strictly using Cost of Delay (CoD) divided by duration (WSJF).\n\n"
                "3. Sponsor Briefing (35 Marks):\n"
                "Brief the sponsor using a cumulative flow diagram. Demonstrate that engineering capacity was consumed by architectural debt and unvalidated requirements. Present the transition to verified value throughput metrics and show expected stabilization within two cadences."
            ),
        },
    ],
    'starting-a-project': [
        {
            'order': 1,
            'title': 'Strategic Alignment, Business Case Feasibility & ESG Value Delivery Frameworks',
            'synopsis': 'Translating corporate strategic plans into defensible project boundaries, commercial justification, and ESG mandates.',
            'notes': (
                "1. Strategic Alignment Scoring: Evaluating Net Present Value (NPV), Internal Rate of Return (IRR), and Strategic Fit.\n"
                "2. PMBOK 8th Edition ESG Alignment: Incorporating decarbonization, social governance, and sustainable procurement into project initiation.\n"
                "3. Boundary Defense: Explicitly defining Out-of-Scope operational handoffs to prevent early-stage creep."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A regional commercial bank is initiating a $2.5M multi-branch digital onboarding transformation. "
                "The business case promises a 22% reduction in branch operational expenditure within 18 months. "
                "However, executive stakeholders are attempting to inject call-center system overhauls and legacy ATM upgrades into the project scope.\n\n"
                "Candidate Assignment:\n"
                "1. Formulate the Project Scope Boundary Statement, explicitly detailing 3 In-Scope deliverables and 3 Out-of-Scope exclusions.\n"
                "2. Define two ESG metrics integrated into vendor evaluation criteria.\n"
                "3. Calculate the Payback Period if the project generates $750,000 in operational savings annually starting year 1."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Scope Boundaries (40 Marks):\n"
                "• In-Scope: Mobile account onboarding PWA, biometric e-KYC integration with national identity databases, automated core banking webhook connector.\n"
                "• Out-of-Scope: Legacy ATM firmware upgrades, physical call-center telephony routing overhauls, manual in-branch paper teller processing.\n\n"
                "2. ESG Procurement Criteria (30 Marks):\n"
                "Mandate that software hosting infrastructure utilizes 100% renewable energy data centers (PUE < 1.2), and vendor contracts enforce zero-electronic-waste disposal certifications for decommissioned biometric scanners.\n\n"
                "3. Payback Period Calculation (30 Marks):\n"
                "Payback Period = Initial Investment / Annual Cash Flow = $2,500,000 / $750,000 = 3.33 Years (3 Years, 4 Months)."
            ),
        },
        {
            'order': 2,
            'title': 'Project Charter Architecture, Multi-Tier Delegated Authority & Sponsor Governance',
            'synopsis': 'Authoring enforceable project charters, mapping power grids, and locking executive sponsor authority delegations.',
            'notes': (
                "1. PMBOK 8th Edition Charter Components: Purpose, Success Criteria, Measurable Objectives, and Executive Sign-off.\n"
                "2. Delegated Financial Authority Matrix: Setting thresholds for autonomous PM variance approval versus Board escalations.\n"
                "3. Sponsor Relationship Governance: Aligning steering committee cadence with strategic value realization checkpoints."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "You are drafting the Project Charter for a $1.2M municipal solar microgrid installation. "
                "The municipal council demands final approval on every contractor expense exceeding $5,000, "
                "which would paralyze procurement and delay civil works by 8 weeks.\n\n"
                "Candidate Assignment:\n"
                "1. Draft the Delegated Authority Section of the Charter establishing defensible thresholds for the Project Manager.\n"
                "2. Define the formal Steering Committee escalation threshold for schedule and cost baselines.\n"
                "3. Author the Executive Sponsor Commitment Clause binding governance sponsors to 5-day review turnarounds."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Delegated Authority Thresholds (35 Marks):\n"
                "• Autonomous PM Authority: Sole sign-off on budgeted procurement line items up to $50,000.\n"
                "• Schedule Discretion: Authority to reallocate project float up to 10 working days without steering escalation.\n"
                "• Contingency Reserve Access: PM authorized to deploy up to $25,000 from approved contingency for verified critical path threats.\n\n"
                "2. Steering Committee Escalation (35 Marks):\n"
                "Any change request impacting total project cost by > 3% ($36,000), shifting contractual grid tie-in milestones by > 15 days, or altering statutory environmental permits requires formal Steering Committee majority vote.\n\n"
                "3. Sponsor SLA Commitment Clause (30 Marks):\n"
                "'The Executive Sponsor covenants to review and formally resolve submitted Stage-Gate dossiers, ICC escalations, and critical risk decisions within 5 business days of receipt. Inactions exceeding 5 days automatically grant the PM authorization to proceed under documented provisional assumptions.'"
            ),
        },
    ],
    'planning-a-project': [
        {
            'order': 1,
            'title': '100% Rule Work Breakdown Structures (WBS), Scope Baselines & AI Scope Validation',
            'synopsis': 'Decomposing complex deliverables into verifiable work packages without omissions or overlaps using PMBOK 8th Edition rigor.',
            'notes': (
                "1. The 100% Rule: Covering all product, project, and PM deliverables without gaps or duplication.\n"
                "2. The 8/80 Heuristic: Work package duration boundary between 8 hours and 80 hours of single-owner effort.\n"
                "3. Scope Baseline Components: Approved Scope Statement, WBS, and WBS Dictionary with verifiable acceptance criteria."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A government healthcare agency is implementing a Telemedicine Video Consultation Platform. "
                "During planning, the technical team presents a functional deliverable list, but omits clinical data privacy audit compliance, "
                "doctor onboarding training, and disaster recovery replication.\n\n"
                "Candidate Assignment:\n"
                "1. Construct a 3-level WBS for Deliverable 2.0 (Clinical Telemedicine Platform) incorporating the omitted packages.\n"
                "2. Author the complete WBS Dictionary entry for Package 2.3.1 (HIPAA/GDPR Security Audit Gate).\n"
                "3. Explain how the 100% Rule defends the budget baseline against unanticipated vendor claims."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. 3-Level WBS Decomposition (35 Marks):\n"
                "2.0 Clinical Telemedicine Platform\n"
                "  2.1 Core Consultation Engine\n"
                "    2.1.1 WebRTC Video Consultation Service\n"
                "    2.1.2 Clinical Notes & Prescription Module\n"
                "  2.2 Platform Security & Data Integrity\n"
                "    2.2.1 End-to-End Encryption Layer\n"
                "    2.2.2 Disaster Recovery & Multi-Region Hot-Failover\n"
                "  2.3 Statutory Compliance & Verification\n"
                "    2.3.1 HIPAA/GDPR Third-Party Security Audit Gate\n"
                "  2.4 Operational Enablement\n"
                "    2.4.1 Clinician Workflow Certification & Training Curriculum\n\n"
                "2. WBS Dictionary Entry 2.3.1 (35 Marks):\n"
                "• Work Package Title: HIPAA/GDPR Third-Party Security Audit Gate\n"
                "• Owner: Lead Information Security Officer\n"
                "• Deliverable: Independent certified audit penetration test report with zero critical or high vulnerabilities.\n"
                "• Acceptance Criteria: Formal ISO/IEC 27001 compliance certificate and signed Ministry Health Data Protection clearance.\n"
                "• Duration: 15 Working Days | Cost Baseline: $35,000.\n\n"
                "3. Baseline Defense via 100% Rule (30 Marks):\n"
                "Because the WBS encompasses 100% of the contractual scope, anything absent from the WBS is contractually non-existent in the baseline. Any external demand for unlisted work automatically constitutes a formal change request subject to additional billing and schedule extension."
            ),
        },
        {
            'order': 2,
            'title': 'Critical Path Method (CPM), Schedule Dynamics & Float Preservation under Uncertainty',
            'synopsis': 'Precedence Diagramming Method (PDM), forward/backward pass calculations, critical path identification, and schedule crashing.',
            'notes': (
                "1. Precedence Diagramming Method (PDM): FS, FF, SS, SF relationships with Lead and Lag times.\n"
                "2. Float Calculations: Total Float (LS - ES) vs Free Float (ES of successor - EF - lag).\n"
                "3. Schedule Compression Trade-Offs: Fast-tracking (increases risk and rework) versus Crashing (increases cost)."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A project schedule network has the following critical path activities:\n"
                "• Activity A (Site Preparation): Duration = 4 days, Cost = $10,000\n"
                "• Activity B (Foundation Pour): Duration = 6 days, Crash Duration = 4 days, Crash Cost = $8,000/day\n"
                "• Activity C (Structural Erection): Duration = 8 days, Crash Duration = 5 days, Crash Cost = $5,000/day\n"
                "A delay of 3 days occurs on Activity A due to severe flooding.\n\n"
                "Candidate Assignment:\n"
                "1. Calculate the impact of Activity A's delay on the project completion milestone.\n"
                "2. Formulate the most cost-effective crashing strategy to recover the 3 days lost.\n"
                "3. Calculate the total cost increase to the project baseline."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Delay Milestone Impact (30 Marks):\n"
                "Because Activity A resides on the Critical Path with 0 Total Float, an unmitigated 3-day delay on Activity A directly pushes the entire project completion milestone out by exactly 3 days.\n\n"
                "2. Optimal Crashing Strategy (40 Marks):\n"
                "To recover 3 days at lowest marginal cost:\n"
                "• Compare crash cost per day on critical path: Activity C ($5,000/day) vs Activity B ($8,000/day).\n"
                "• Activity C has 3 days of available crash capacity (8 days down to 5 days).\n"
                "• Action: Crash Activity C by exactly 3 days at $5,000/day. (Do not crash Activity B, which is more expensive).\n\n"
                "3. Baseline Budget Impact (30 Marks):\n"
                "Total additional crashing cost = 3 days x $5,000/day = $15,000. Project completion date is preserved at baseline with a $15,000 drawdown on the contingency reserve."
            ),
        },
    ],
    'executing-a-project': [
        {
            'order': 1,
            'title': 'Dynamic Change Governance, Impact Modeling & Integrated Change Control (ICC)',
            'synopsis': 'PMBOK 8th Edition change impact assessment, Change Control Board (CCB) mechanics, and contractual baseline defense.',
            'notes': (
                "1. Integrated Change Control 5-Step Discipline: Log, Analyze Impact, Consult Sponsor/CCB, Decide, Re-baseline.\n"
                "2. Multi-Constraint Impact Analysis: Modeling downstream cost, schedule, risk, quality, and resource capacity ripples.\n"
                "3. Managing Client Pressure: Techniques for resisting informal, undocumented scope injection on the field."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "During execution of a modern corporate enterprise ERP rollout, the Chief Financial Officer (CFO) directs the lead database engineer "
                "to implement an unbudgeted multi-currency automated tax reporting module within 2 weeks, stating 'the Board expects this on launch day.'\n\n"
                "Candidate Assignment:\n"
                "1. Detail your immediate 24-hour response to both the engineer and the CFO.\n"
                "2. Execute a formal Triple-Constraint impact assessment assuming the change requires $30,000 and 12 developer-days.\n"
                "3. Author the formal CCB decision memorandum presenting the sponsor with trade-off choices."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Immediate 24-Hour Response (30 Marks):\n"
                "• Engineer: Direct the engineer to pause work immediately; explain that unapproved changes violate configuration governance.\n"
                "• CFO: Meet privately with the CFO. Acknowledge strategic importance, log request as CR-042, and explain that formal impact modeling is underway for CCB review.\n\n"
                "2. Triple-Constraint Impact Analysis (35 Marks):\n"
                "• Cost: +$30,000 direct engineering expense + $5,000 compliance auditing = +$35,000 total.\n"
                "• Schedule: Consumes 12 developer-days from the critical path, delaying system integration testing by 8 business days.\n"
                "• Quality & Risk: Introduces high risk of integration defects due to compressed testing cycles; requires re-certification of tax calculations.\n\n"
                "3. CCB Memorandum Options (35 Marks):\n"
                "Present 2 viable pathways: Option A: Approve CR-042 with +$35,000 funding and push go-live date out by 10 days; Option B: Defer CR-042 to Phase 1.1 release (30 days post-launch) preserving current go-live baseline and budget."
            ),
        },
    ],
    'closing-a-project': [
        {
            'order': 1,
            'title': 'Formal Handover, Value Realization Audits & Contractual Claims Settlement',
            'synopsis': 'Securing signed Certificate of Practical Completion, clearing punch-lists, and closing multi-million procurement contracts.',
            'notes': (
                "1. PMBOK 8th Edition Value Handover: Transitioning deliverables into operations with verified adoption metrics.\n"
                "2. Punch-List Resolution Mechanics: Distinguishing cosmetic snags from material non-compliance.\n"
                "3. Procurement Contract Closeout: Formal subcontractor lien waivers, warranties transfer, and retention release."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A corporate commercial headquarters building project reaches substantial completion. "
                "The client demands handover keys but refuses to sign the Certificate of Practical Completion, "
                "citing minor paint scuffs in the basement parking lot and requesting uncontracted solar canopy installations.\n\n"
                "Candidate Assignment:\n"
                "1. Establish the legal and contractual distinction between Practical Completion and Minor Punch-List Items.\n"
                "2. Author the clause in the Handover Protocol resolving the painting snags while protecting retention funds.\n"
                "3. Formulate your contractual rejection of the client's out-of-scope solar canopy demand."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Contractual Distinction (35 Marks):\n"
                "Practical Completion occurs when the facility is fit for its intended commercial occupancy and operation, notwithstanding minor cosmetic snags that do not prevent safe tenant use. Paint scuffs are minor punch-list defects, not grounds to withhold completion certification.\n\n"
                "2. Handover Protocol Resolution (35 Marks):\n"
                "Incorporate a 14-day Snagging Resolution Undertaking. Retain a capped $5,000 escrow from the final billing specifically earmarked for painting touch-ups, and mandate simultaneous execution of the Certificate of Practical Completion releasing 50% of statutory retention.\n\n"
                "3. Rejection of Scope Claim (30 Marks):\n"
                "'The solar canopies requested constitute new capital works absent from Contract Annexure B (Approved Specifications). These works cannot be linked to Phase 1 handover. Project Focus welcomes the opportunity to quote these canopies as a distinct Phase 2 project under separate procurement terms.'"
            ),
        },
    ],
    'building-an-empowered-team-culture': [
        {
            'order': 1,
            'title': 'Psychological Safety Architecture, Decentralized Governance & Blameless Post-Mortems',
            'synopsis': 'Building a high-accountability delivery culture where critical project risks and architectural errors are surfaced instantly.',
            'notes': (
                "1. Amy Edmondson's 3 Pillars: Framing work as learning challenges, acknowledging fallibility, and modeling curiosity.\n"
                "2. Decentralized Decision Frameworks: Using Delegation Poker and RACI-Matrix to empower autonomous frontline action.\n"
                "3. Blameless Retrospective Protocols: Isolating system and environmental defects rather than scapegoating team members."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "During a critical database upgrade, an associate systems engineer executes an untested SQL script that wipes 4 hours of production transaction records. "
                "The engineering manager publicly berates the associate in the team chat and demands their termination.\n\n"
                "Candidate Assignment:\n"
                "1. Intervene as Project Director to de-escalate the public shaming and re-establish psychological safety.\n"
                "2. Structure the formal 5-Whys root cause analysis demonstrating the systemic procedural breakdown.\n"
                "3. Implement two automated guardrails preventing recurrence without restricting developer autonomy."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Director Intervention (30 Marks):\n"
                "Immediately move conversation to private channel. State publicly: 'Human execution errors reflect systemic testing and safeguard omissions. We evaluate processes, not punish individuals.' Affirm team safety while initiating automated backup restoration.\n\n"
                "2. 5-Whys Root Cause Analysis (35 Marks):\n"
                "• Why 1: Transactions wiped? Untested script executed directly in production.\n"
                "• Why 2: Script untested? No isolated staging database mirrored production schemas.\n"
                "• Why 3: Executed directly? Production credentials were embedded in developer environments.\n"
                "• Why 4: No access restriction? PMO lacked role-based privileged identity access controls.\n"
                "• Why 5 (Root Cause): Deployment pipeline lacked automated peer-review and staging gate automation.\n\n"
                "3. Systemic Guardrails (35 Marks):\n"
                "Revoke production write credentials from individual workstations. Enforce automated CI/CD pipeline deployment requiring two independent peer approvals and mandatory automated rollback snapshots prior to database execution."
            ),
        },
    ],
    'managing-project-risk': [
        {
            'order': 1,
            'title': 'Quantitative Risk Modeling, Expected Monetary Value (EMV) & AI Predictive Risk Triggers',
            'synopsis': 'Calculating probability-weighted financial exposure, sizing contingency reserves, and monitoring early-warning risk telemetry.',
            'notes': (
                "1. PMBOK 8th Edition Quantitative Modeling: Expected Monetary Value (EMV = Probability x Financial Impact).\n"
                "2. Reserve Sizing: Contingency Reserves (Known Unknowns - PM controlled) vs Management Reserves (Unknown Unknowns - Sponsor controlled).\n"
                "3. Risk Trigger Telemetry: Establishing leading technical and commercial indicators to launch proactive response strategies."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "You are directing a $4,000,000 fiber-optic infrastructure deployment across 12 municipalities. "
                "Your risk register identifies two critical threats and one opportunity during horizontal drilling:\n"
                "• Risk 1 (Underground Utility Strike): Probability = 25%, Impact = $120,000 in repair fines and delay.\n"
                "• Risk 2 (Permit Approval Delay): Probability = 40%, Impact = $60,000 in idling equipment costs.\n"
                "• Opportunity 1 (Bulk Subcontracting Discount): Probability = 50%, Benefit = $80,000 in cost savings.\n\n"
                "Candidate Assignment:\n"
                "1. Calculate the Expected Monetary Value (EMV) for each event and determine the Net Project Contingency Reserve required.\n"
                "2. Formulate a Risk Mitigation Strategy for Risk 1 that reduces probability to 5% at a cost of $10,000.\n"
                "3. Perform a financial cost-benefit analysis confirming whether the mitigation is economically justified."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. EMV & Reserve Calculations (35 Marks):\n"
                "• EMV(Risk 1) = 0.25 x $120,000 = $30,000.\n"
                "• EMV(Risk 2) = 0.40 x $60,000 = $24,000.\n"
                "• EMV(Opportunity 1) = 0.50 x (-$80,000) = -$40,000.\n"
                "• Net Project Contingency Reserve = $30,000 + $24,000 - $40,000 = $14,000.\n\n"
                "2. Mitigation Strategy for Risk 1 (35 Marks):\n"
                "Deploy ground-penetrating radar (GPR) pre-drilling scans and require certified municipal utility marking prior to drilling commencement. Cost of GPR service = $10,000.\n\n"
                "3. Cost-Benefit Economic Validation (30 Marks):\n"
                "• Unmitigated EMV = $30,000.\n"
                "• Mitigated EMV = (0.05 x $120,000) + $10,000 mitigation expense = $6,000 + $10,000 = $16,000.\n"
                "• Net Financial Benefit = $30,000 - $16,000 = $14,000 savings. Mitigation is overwhelmingly justified."
            ),
        },
    ],
    'project-performance-management': [
        {
            'order': 1,
            'title': 'Earned Value Management (EVM) Analytics, EAC Forecasting & Root-Cause CAPA Mechanics',
            'synopsis': 'Calculating PV, EV, AC, CPI, SPI, EAC, and TCPI to diagnose baseline trajectory and prescribe corrective actions.',
            'notes': (
                "1. Core EVM Equations: CV = EV - AC; SV = EV - PV; CPI = EV / AC; SPI = EV / PV.\n"
                "2. Estimate at Completion (EAC) Forecasting: EAC = BAC / CPI (at current efficiency); EAC = AC + (BAC - EV) (unusual variance).\n"
                "3. To-Complete Performance Index (TCPI): Work Remaining / Funds Remaining = (BAC - EV) / (BAC - AC)."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "You are auditing a civil capital project at the end of Month 6. "
                "• Budget at Completion (BAC) = $1,000,000\n"
                "• Planned Value (PV) = $600,000\n"
                "• Earned Value (EV) = $480,000\n"
                "• Actual Cost (AC) = $540,000\n\n"
                "Candidate Assignment:\n"
                "1. Calculate the Cost Variance (CV), Schedule Variance (SV), CPI, and SPI. State the dual project health status.\n"
                "2. Forecast the Estimate at Completion (EAC) assuming performance continues at current cost efficiency.\n"
                "3. Calculate the To-Complete Performance Index (TCPI) required to finish within the original $1,000,000 budget and evaluate feasibility."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. EVM Metric Calculations (35 Marks):\n"
                "• CV = EV - AC = $480,000 - $540,000 = -$60,000 (Over budget by $60,000).\n"
                "• SV = EV - PV = $480,000 - $600,000 = -$120,000 (Behind schedule by $120,000 worth of work).\n"
                "• CPI = EV / AC = $480,000 / $540,000 = 0.889.\n"
                "• SPI = EV / PV = $480,000 / $600,000 = 0.800.\n"
                "Status: Project is simultaneously over budget (CPI < 1.0) and severely behind schedule (SPI < 1.0).\n\n"
                "2. EAC Forecast (35 Marks):\n"
                "EAC = BAC / CPI = $1,000,000 / 0.889 = $1,124,859. The project is forecasted to exceed approved budget by $124,859.\n\n"
                "3. TCPI & Feasibility (30 Marks):\n"
                "TCPI = (BAC - EV) / (BAC - AC) = ($1,000,000 - $480,000) / ($1,000,000 - $540,000) = $520,000 / $460,000 = 1.13.\n"
                "Feasibility Assessment: To achieve original budget, the team must immediately operate at 113% efficiency (a 24% jump from current 89%). This is historically unfeasible without structural intervention (scope reduction or capital injection)."
            ),
        },
    ],
    'engaging-project-stakeholders': [
        {
            'order': 1,
            'title': 'Boardroom Steering Diagnostics, Power/Interest Networks & Political Alignment',
            'synopsis': 'Managing executive stakeholder politics, navigating sponsor turnover, and converting resistant executives into champions.',
            'notes': (
                "1. PMBOK 8th Edition Stakeholder Engagement Matrix: Unaware, Resistant, Neutral, Supportive, Leading.\n"
                "2. Salience Model Diagnostics: Power, Legitimacy, and Urgency identification for boardroom influence.\n"
                "3. Executive Communication Architecture: Designing 3-slide decision dashboards that drive boardroom alignment."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A hospital electronic medical records modernization initiative is threatened by the Chief Medical Officer (High Power, High Influence), "
                "who publicly denounces the software as 'an administrative burden that slows down patient triage,' actively urging surgeons to boycott training.\n\n"
                "Candidate Assignment:\n"
                "1. Map the Chief Medical Officer using the Salience Model and explain why traditional email memos fail.\n"
                "2. Construct a tailored 3-point Stakeholder Engagement Strategy converting the CMO from Resistant to Supportive.\n"
                "3. Detail the specific clinical governance concessions you are prepared to offer without compromising core project scope."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Salience Model Diagnosis (30 Marks):\n"
                "The CMO is a 'Definitive Stakeholder' possessing Power (command over clinical staff), Legitimacy (clinical safety champion), and Urgency (immediate patient care impact). Generic PMO broadcast memos fail because they treat clinical leadership as passive administrative recipients rather than sovereign decision-makers.\n\n"
                "2. Engagement Intervention (35 Marks):\n"
                "• Direct 1-on-1 Discovery: Meet the CMO in the clinical ward, not in the PMO office, observing triage friction firsthand.\n"
                "• Co-Design Governance: Appoint the CMO as Co-Chair of the Clinical Informatics Steering Committee with direct veto over UX triage flows.\n"
                "• Pilot Slicing: Isolate emergency triage workflows from general admissions, offering a bespoke, customized quick-entry screen.\n\n"
                "3. Defensible Concessions (35 Marks):\n"
                "Concede 3 non-regulatory data-entry fields, implement voice-to-text transcription plugins, and hire 2 medical scribes during the first 14 days of launch to absorb physician administrative overhead while patient records baseline."
            ),
        },
    ],
    'project-metrics-and-reporting': [
        {
            'order': 1,
            'title': 'Executive PMO Telemetry, Automated Flow Dashboards & Board Scorecard Engineering',
            'synopsis': 'Replacing subjective RAG status reports with automated PMO telemetry, lead/lag indicators, and variance forecasting.',
            'notes': (
                "1. The Failure of Subjective RAG Statusing: Eliminating the 'Watermelon Phenomenon' (Green on outside, Red on inside).\n"
                "2. Leading Indicators (Risk Velocity, Requirement Churn, Team WIP) vs Lagging Indicators (Actual Cost, Milestones Missed).\n"
                "3. Designing Executive Telemetry: Real-time data connectors feeding PowerBI/Tableau directly from project repositories."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A Project Manager has submitted 4 consecutive monthly status reports marked 'GREEN'. "
                "On Week 20, the project abruptly announces an 8-week schedule delay and a $140,000 budget deficit due to supplier stockouts. "
                "The Board of Directors demands immediate overhaul of PMO reporting standards.\n\n"
                "Candidate Assignment:\n"
                "1. Diagnose how subjective status reporting masked delivery reality (the Watermelon Project).\n"
                "2. Engineer a new Executive Telemetry Scorecard selecting 2 objective leading indicators and 2 objective lagging indicators.\n"
                "3. Establish the mandatory automated trigger criteria that forces an automated 'AMBER' or 'RED' status regardless of PM opinion."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Watermelon Failure Analysis (30 Marks):\n"
                "Subjective RAG reporting allowed the PM to evaluate status based on optimistic intent rather than objective data. The absence of verifiable telemetry decoupled milestone reporting from actual inventory supply chain lead-times, keeping the exterior 'Green' until schedule failure was unavoidable.\n\n"
                "2. Executive Scorecard Design (35 Marks):\n"
                "• Leading Indicator 1: Supplier Purchase Order Lead-Time Variance (Tracking supplier delivery commitment vs published baseline).\n"
                "• Leading Indicator 2: Work-In-Progress (WIP) Aging (Tasks in progress > 150% of planned duration).\n"
                "• Lagging Indicator 1: Cost Performance Index (CPI = EV / AC calculated strictly from verified contractor deliverables).\n"
                "• Lagging Indicator 2: Critical Path Milestone Float Variance (Days of float lost per reporting period).\n\n"
                "3. Objective Red-Flag Rules (35 Marks):\n"
                "• Systemic AMBER: CPI or SPI drops between 0.90 and 0.95, or total critical path float drops by > 5 working days.\n"
                "• Mandatory RED: CPI or SPI < 0.90, critical path float equals zero with pending variance, or any unmitigated risk with financial exposure exceeding 50% of remaining contingency reserve."
            ),
        },
    ],
    'managing-project-knowledge': [
        {
            'order': 1,
            'title': 'Tacit Knowledge Retention, Architecture Decision Records (ADR) & Institutional SOPs',
            'synopsis': 'Preventing organizational brain-drain, capturing field heuristics, and transforming retrospective learnings into standard SOPs.',
            'notes': (
                "1. Nonaka-Takeuchi Knowledge Model: Converting Tacit knowledge (field heuristics) into Explicit knowledge (reusable SOPs).\n"
                "2. Architecture Decision Records (ADR): Documenting context, choices, trade-offs, and consequences of critical decisions.\n"
                "3. Institutional Memory Repositories: Establishing searchable PMO playbooks to prevent repeating past project mistakes."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "The Lead Construction Resident Engineer who has overseen 15 consecutive substation installations is retiring in 30 days. "
                "All historical equipment commissioning tricks, local utility bypass procedures, and inspector relationships reside exclusively in the engineer's memory.\n\n"
                "Candidate Assignment:\n"
                "1. Formulate a 4-week Tacit Knowledge Capture Plan pairing the veteran with a junior project engineer.\n"
                "2. Author an Architecture Decision Record (ADR) template capturing why a specific technical trade-off was executed.\n"
                "3. Institutionalize these insights into a mandatory PMO Stage-Gate Inspection SOP."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. 4-Week Knowledge Extraction Plan (35 Marks):\n"
                "• Week 1: Cognitive Task Analysis & Job Shadowing during live field inspections.\n"
                "• Week 2: Video-recorded walkthroughs of complex substation calibration and undocumented local utility interface steps.\n"
                "• Week 3: Reverse-Shadowing where the junior engineer leads commissioning while the veteran critiques and refines decisions.\n"
                "• Week 4: Joint authoring of the 'Substation Commissioning Field Heuristics Playbook' and formal stakeholder introductions.\n\n"
                "2. ADR Structure (35 Marks):\n"
                "• Context: Detail environmental/regulatory constraints necessitating decision.\n"
                "• Decision: Concrete technical architecture or methodology selected.\n"
                "• Alternatives Evaluated: What other solutions were rejected and why.\n"
                "• Consequences: Downstream risks, trade-offs, and maintenance requirements accepted.\n\n"
                "3. SOP Institutionalization (30 Marks):\n"
                "Embed captured heuristics as mandatory pre-commissioning checklist gates in the PMO enterprise management portal. Milestone sign-off cannot proceed without verified compliance with the documented checklist."
            ),
        },
    ],
    'project-compliance-and-sustainability': [
        {
            'order': 1,
            'title': 'ESG Governance Baselines, Statutory Audit Gates & Circular Project Economics',
            'synopsis': 'Integrating Environmental, Social, and Governance (ESG) standards with regulatory integrity and statutory audit defenses.',
            'notes': (
                "1. PMBOK 8th Edition Sustainability Principles: Environmental stewardship, decarbonization, and fair labor governance.\n"
                "2. Statutory Compliance Gates: Mandatory environmental impact assessments, permitting cadences, and legal hold points.\n"
                "3. Defending Regulatory Audits: Maintaining contemporaneous project records that withstand scrutiny from international oversight bodies."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "A $10,000,000 public-private partnership (PPP) port expansion project is audited by the Environmental Protection Agency (EPA). "
                "The auditor discovers that a dredging subcontractor disposed of seabed spoil in an unauthorized coastal zone, "
                "threatening the project with immediate suspension and a $500,000 statutory fine.\n\n"
                "Candidate Assignment:\n"
                "1. Outline your immediate crisis response within 24 hours to address the regulatory authority and protect project continuity.\n"
                "2. Conduct a Contractual Indemnity Review determining whether the prime contractor or the subcontractor bears financial liability.\n"
                "3. Institute an automated IoT/telemetry compliance gate to prevent unauthorized equipment operation."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. 24-Hour Crisis Protocol (35 Marks):\n"
                "Issue an immediate Stop-Work Order to the dredging unit. Formally notify the EPA in writing with complete transparency, acknowledging the incident and presenting an immediate containment plan. Deploy environmental response teams to test water turbidity and remediate spoil.\n\n"
                "2. Contractual Indemnity Defense (35 Marks):\n"
                "Review Subcontractor Agreement Section 14 (Environmental Compliance & Indemnification). Issue formal notice of breach. Because the subcontractor deliberately breached approved disposal coordinates specified in Appendix D, enforce the full hold-harmless indemnity clause, transferring the $500,000 fine and all remediation expenses to the subcontractor.\n\n"
                "3. Telemetry Compliance Gate (30 Marks):\n"
                "Equip all dredging vessels with GPS-geofenced telemetry tracking locks. Dredge hopper discharge doors remain electronically locked by automated software until the GPS receiver confirms vessel coordinates are within the legally designated marine disposal zone."
            ),
        },
    ],
    'cross-mentoring-in-project-teams': [
        {
            'order': 1,
            'title': 'Bidirectional Mentoring: Pairing Legacy Engineering Wisdom with Digital PMO AI Tools',
            'synopsis': 'Pairing seasoned veteran engineers with agile digital practitioners to eliminate silos and preserve institutional memory.',
            'notes': (
                "1. Two-Way Mentoring Architecture: Senior managers provide political and contract wisdom; digital leads teach automation and AI.\n"
                "2. Reverse Mentoring Dynamics: Establishing non-hierarchical learning partnerships that dismantle generational resistance.\n"
                "3. Collaborative Delivery Milestones: Pairing mentors/mentees on high-stakes WBS deliverables."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "An aerospace manufacturing enterprise is transitioning from paper-based waterfall controls to an automated Jira/AI telemetry PMO. "
                "Senior engineering directors with 25+ years tenure are openly hostile to the new software, while junior Scrum Masters lack "
                "the contractual knowledge to negotiate scope disputes with government auditors.\n\n"
                "Candidate Assignment:\n"
                "1. Design a 6-week Bidirectional Cross-Mentoring Cohort pairing senior directors with digital Scrum Masters.\n"
                "2. Establish the weekly curriculum balancing technical digital workflow training with executive contract negotiation.\n"
                "3. Formulate the evaluation criteria that proves the mentoring program improved delivery performance."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Cohort Design (35 Marks):\n"
                "Pair each Senior Director 1-on-1 with an Agile/Digital PM practitioner. Establish mutual accountability: 90-minute weekly sessions, alternating weekly lead instructor roles to eliminate power differentials and foster psychological safety.\n\n"
                "2. 6-Week Curriculum Architecture (35 Marks):\n"
                "• Week 1: Reciprocal Capability Mapping & Trust Charter.\n"
                "• Week 2: Digital PM trains Veteran on automated Jira backlog telemetry and AI prompt drafting for project documentation.\n"
                "• Week 3: Veteran trains Digital PM on FAR/FIDIC contractual dispute clauses and client steering diplomacy.\n"
                "• Week 4: Digital PM configures an automated dashboard specifically tracking the Veteran's live project portfolio.\n"
                "• Week 5: Veteran coaches Digital PM through a mock adversarial CCB change-order negotiation.\n"
                "• Week 6: Co-presentation of an executive project update to the Corporate Board.\n\n"
                "3. Performance Metrics (30 Marks):\n"
                "Measure success via: 50% reduction in paper change order cycle time, 100% adoption of digital dashboards by veteran directors, and zero audit non-compliance citations on junior PM projects."
            ),
        },
    ],
    'collaborating-in-projects': [
        {
            'order': 1,
            'title': 'Cross-Functional Interface Agreements (IA), Dependency Matrix & Silo Elimination',
            'synopsis': 'Eliminating departmental friction between engineering, procurement, legal, and operational units during project handoffs.',
            'notes': (
                "1. PMBOK 8th Edition Systems Integration: Treating cross-functional departments as unified value delivery streams.\n"
                "2. Interface Agreements (IA): Legally structured internal SLAs establishing input/output delivery standards between units.\n"
                "3. Cross-Departmental Dependency Mapping: Using Dependency Matrices to identify hidden critical path choke-points."
            ),
            'task': (
                "Practical Executive Scenario:\n"
                "On a major industrial refinery automation project, Engineering consistently delivers technical bills-of-materials 3 weeks late. "
                "In retaliation, Procurement withholds component order tracking numbers, leaving Field Construction idle on site. "
                "Department heads blame each other during executive committee meetings.\n\n"
                "Candidate Assignment:\n"
                "1. Draft an enforceable Cross-Functional Interface Agreement (IA) between Engineering and Procurement.\n"
                "2. Construct the Inter-Departmental Dependency Escalation Matrix with explicit SLA timelines.\n"
                "3. Define the financial governance consequence when one department breaches interface delivery dates."
            ),
            'solution': (
                "Official Marking Rubric & Solution Guide:\n\n"
                "1. Interface Agreement (IA) Framework (35 Marks):\n"
                "• Input Specification: Engineering must deliver 100% locked equipment specifications in standardized CSV/BOM format exactly 20 business days prior to scheduled procurement windows.\n"
                "• Output SLA: Procurement must issue competitive RFQs within 5 business days of specification lock and publish real-time vendor tracking telemetry accessible to Engineering and Field Leads.\n\n"
                "2. Dependency Escalation Protocol (35 Marks):\n"
                "• Day 1 Variance: Automated alert dispatched to both Department Leads upon missing BOM deadline.\n"
                "• Day 3 Variance: Mandatory standing standup convened by PMO Director to re-baseline internal priorities.\n"
                "• Day 5 Variance: Immediate escalation to Chief Operating Officer (COO); unapproved delays result in re-allocation of department overtime budget.\n\n"
                "3. Governance Financial Accountability (30 Marks):\n"
                "Idling costs of field crews resulting from unnotified department handoff failures are formally recorded as internal variance against the offending department's overhead cost center, directly impacting annual departmental performance scorecards."
            ),
        },
    ],
    'pmp-exam-mastery': [
        {
            'order': 1,
            'title': 'Project Foundations, Systems Thinking & Complex Adaptive Lifecycles',
            'synopsis': 'PMBOK 8th Edition core foundational principles, value stream networks, and complex systems project governance.',
            'notes': (
                "1. PMBOK 8th Edition Paradigm: Transition from rigid procedural domains to Complex Adaptive Systems (CAS) thinking.\n"
                "2. Value Delivery Networks: Projects as dynamic value generation engines delivering organizational capability.\n"
                "3. Stewardship, Governance & Systems Facilitation: Aligning project objectives with enterprise strategy and societal ethics."
            ),
            'task': (
                "PMP® Situational Exam Scenario (Domain I & II - PMBOK 8th Edition Aligned):\n"
                "An international technology consortium is delivering an autonomous public transportation system in a major smart city. "
                "Statutory safety regulators introduce real-time cybersecurity compliance standards mid-stream. "
                "The project team consists of traditional hardware engineers who want to freeze design, and AI software teams who iterate weekly.\n\n"
                "Candidate Question:\n"
                "What is the Project Director's FIRST action to establish systems alignment across these conflicting delivery models?\n"
                "A. Instruct the AI software team to halt iterations and follow the predictive hardware schedule.\n"
                "B. Submit a formal change request to the steering committee to remove the cybersecurity regulation.\n"
                "C. Architect a hybrid delivery model establishing fixed predictive safety gates with adaptive software iterations.\n"
                "D. Direct the regulatory agency to postpone safety compliance until Phase 2 commercial commissioning."
            ),
            'solution': (
                "Correct Answer: C\n\n"
                "Examination Rationale (PMBOK® 8th Edition):\n"
                "• Option C is correct: PMBOK 8th Edition emphasizes Systems Thinking and Adaptive Tailoring. In complex cyber-physical initiatives, hybrid lifecycles are the standard: predictive rigor for physical hardware safety baselines, combined with iterative agile cadences for software and cybersecurity updates.\n"
                "• Option A is incorrect: Forcing modern AI telemetry into waterfall schedules destroys delivery velocity and responsiveness.\n"
                "• Option B and D are incorrect: Statutory compliance and public safety regulations are mandatory non-negotiable project boundaries; a project manager cannot unilaterally bypass or postpone regulatory law."
            ),
        },
        {
            'order': 2,
            'title': 'Hybrid Lifecycle Tailoring, Flow Metrics & Value Delivery Streams',
            'synopsis': 'Tailoring project lifecycles, integrating predictive stage-gates with agile sprints, and managing Little’s Law flow metrics.',
            'notes': (
                "1. Tailoring Factors: Project complexity, regulatory volatility, organizational culture, and commercial risk.\n"
                "2. Flow Telemetry: Measuring Throughput, Work-In-Progress (WIP), Cycle Time, and Lead Time.\n"
                "3. Stage-Gate Synchronization: Aligning rolling-wave sprint backlogs with formal contractual disbursement gates."
            ),
            'task': (
                "PMP® Situational Exam Scenario (Domain II - Process & Tailoring):\n"
                "A hybrid delivery project has an average Work-In-Progress (WIP) of 30 user stories. Over the last 4 iterations, "
                "the average cycle time per story has doubled from 5 days to 10 days, while the sprint completion throughput dropped by 50%. "
                "Developers state they are constantly multitasking across architectural defects and newly injected features.\n\n"
                "Candidate Question:\n"
                "Which action should the Project Manager execute FIRST to recover flow efficiency according to Little's Law?\n"
                "A. Increase team capacity by adding 4 junior developers to absorb defect tasks.\n"
                "B. Mandate strict Work-In-Progress (WIP) limits across delivery stages and halt new feature starts until blockers clear.\n"
                "C. Extend iteration lengths from 2 weeks to 4 weeks to allow more time for task completion.\n"
                "D. Request an emergency budget increase from the sponsor to compensate for velocity losses."
            ),
            'solution': (
                "Correct Answer: B\n\n"
                "Examination Rationale (PMBOK® 8th Edition):\n"
                "• Option B is correct: Little's Law states that Cycle Time = WIP / Throughput. When cycle time doubles and throughput drops due to multitasking and bottleneck thrashing, the immediate systems remedy is to establish strict WIP limits ('Stop Starting, Start Finishing'), clearing existing work and stabilizing flow.\n"
                "• Option A is incorrect: Adding new personnel to a late or thrashing project increases communication overhead and worsens delay (Brooks's Law).\n"
                "• Option C is incorrect: Extending sprint lengths masks delivery bottlenecks rather than resolving root cause flow friction.\n"
                "• Option D is incorrect: Requesting budget without fixing delivery flow is financial waste."
            ),
        },
    ],
}


# -----------------------------------------------------------------------------
# 3. POPULATE DATABASE WITH PMBOK 8TH EDITION MODULES
# -----------------------------------------------------------------------------
def populate_modules():
    total_created = 0
    total_updated = 0

    corp_category, _ = Category.objects.get_or_create(
        slug='corporate-training',
        defaults={'name': 'Corporate Training', 'description': 'Executive capacity building and PM training.'}
    )

    cert_category, _ = Category.objects.get_or_create(
        slug='certifications',
        defaults={'name': 'Certifications', 'description': 'Professional certification preparation programs.'}
    )

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
        'pmp-exam-mastery': ('Project Management Professional (PMP)® Exam Mastery', 'advanced', 8, 35, 1200),
    }

    for slug, modules_data in CURRICULUM_DATA.items():
        title_info = titles.get(slug, (slug.replace('-', ' ').title(), 'fundamentals', 3, 15, 650))
        target_category = cert_category if slug == 'pmp-exam-mastery' else corp_category

        course = Course.objects.filter(slug=slug).first()
        if not course:
            course = Course.objects.create(
                slug=slug,
                title=title_info[0],
                category=target_category,
                level=title_info[1],
                duration_weeks=title_info[2],
                contact_hours=title_info[3],
                fee=title_info[4],
                tagline=f'PMBOK® Guide 8th Edition aligned professional mastery track for {title_info[0]}.',
                overview=f'Executive project management curriculum delivering systems thinking, value networks, AI telemetry, and adaptive field mechanics for {title_info[0]}.',
                schedule_details='Saturdays: 9:00 AM – 2:00 PM GMT',
                is_active=True,
            )
        else:
            if not course.is_active:
                course.is_active = True
                course.save(update_fields=['is_active'])

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
                    'video_url': mod_info.get('video_url', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'),
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

    print(f"✓ PMBOK 8th Edition population complete: {total_created} modules created, {total_updated} modules updated across courses.")

if __name__ == '__main__':
    print("=" * 70)
    print("Project Focus • PMBOK® 8th Edition Curriculum & Scenario Seeder")
    print("=" * 70)
    patch_allprograms_html()
    populate_modules()
    print("=" * 70)
    print("Curriculum successfully seeded! Refresh your browser to verify.")
    print("=" * 70)