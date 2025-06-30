from django.shortcuts import redirect
from django.urls import reverse
import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
import urllib

class ForzarCambioPasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'userprofile') and request.user.userprofile.must_change_password:
                cambiar_url = reverse('cambiar_password')
                
                # Normaliza para evitar problemas por el slash final
                request_path = request.path.rstrip('/')
                cambiar_path = cambiar_url.rstrip('/')

                if (request_path != cambiar_path 
                    and not request.path.startswith('/admin')
                    and not request.path.startswith('/static/')
                    and not request.path.startswith('/media/')):
                    return redirect('cambiar_password')
                    
        return self.get_response(request)

class InactividadMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(time.time())
            timeout = getattr(settings, 'SESSION_TIMEOUT', 900)
            last_activity = request.session.get('last_activity', now)

            if now - last_activity > timeout:
                logout(request)
                next_url = urllib.parse.quote(request.get_full_path())
                return redirect(f'/login/?next={next_url}')

            request.session['last_activity'] = now

        return self.get_response(request)
