from django.utils import timezone


def quarter_registration_context(request):
    """
    Evaluates the calendar date to determine the active intake quarter (Q1–Q4),
    detects late-quarter intake cutoffs, and provides automatic rollover prompts.
    """
    now = timezone.now()
    year = now.year
    month = now.month
    day = now.day

    # 1. Determine active quarter based on month
    q_num = (month - 1) // 3 + 1
    active_quarter = f"Q{q_num}"
    active_quarter_code = f"Q{q_num} {year}"

    # 2. Quarter end boundaries: Q1 (Mar 31), Q2 (Jun 30), Q3 (Sep 30), Q4 (Dec 31)
    quarter_ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    end_month, end_day = quarter_ends[q_num]

    # 3. Intelligent rollover trigger: True if inside the final 14 days of a quarter
    is_closing_soon = (month == end_month and day >= (end_day - 14))

    # 4. Upcoming quarter calculation
    next_q_num = 1 if q_num == 4 else q_num + 1
    next_year = year + 1 if q_num == 4 else year
    next_quarter_code = f"Q{next_q_num} {next_year}"

    # 5. Dynamic text prompt
    if is_closing_soon:
        prompt_label = f"Final Intake for {active_quarter_code} • Early Enrollment Open for {next_quarter_code}"
    else:
        prompt_label = f"Register for {active_quarter_code} Cohorts"

    return {
        'ACTIVE_QUARTER': active_quarter,
        'ACTIVE_QUARTER_CODE': active_quarter_code,
        'NEXT_QUARTER_CODE': next_quarter_code,
        'REGISTRATION_PROMPT': prompt_label,
        'IS_QUARTER_CLOSING_SOON': is_closing_soon,
        'CURRENT_CALENDAR_YEAR': year,
    }