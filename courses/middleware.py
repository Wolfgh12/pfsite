import time
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect


class SessionIdleTimeoutMiddleware:
    """
    Session inactivity timeout:
    - Director / Staff: 30 minutes (1,800 seconds)[cite: 8]
    - Enrolled Candidates: 30 minutes (1,800 seconds)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = time.time()
            last_activity = request.session.get('last_activity', now)

            # 30 minutes (1,800 seconds) timeout across all accounts
            idle_timeout = 1800

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