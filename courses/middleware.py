import time
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect


class SessionIdleTimeoutMiddleware:
    """
    Tiered session inactivity timeout:
    - Director / Staff: 30 minutes (1,800 seconds)
    - Enrolled Candidates: 2 hours (7,200 seconds)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = time.time()
            last_activity = request.session.get('last_activity', now)

            # 30 mins for Director Mike / Staff; 2 hours for candidates
            idle_timeout = 1800 if request.user.is_staff else 7200

            if (now - last_activity) > idle_timeout:
                is_director = request.user.is_staff or request.path.startswith('/director')
                logout(request)
                request.session.flush()
                messages.warning(request, "Your session expired due to inactivity. Please sign in again.")
                if is_director:
                    return redirect('courses:mike_login')
                return redirect('courses:login')

            request.session['last_activity'] = now

        return self.get_response(request)