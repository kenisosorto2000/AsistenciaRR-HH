from django.shortcuts import redirect
from django.urls import reverse

class ForzarCambioPasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'userprofile') and request.user.userprofile.must_change_password:
                cambiar_url = reverse('cambiar_password')
                if request.path != cambiar_url and not request.path.startswith('/admin'):
                    return redirect('cambiar_password')
        return self.get_response(request)
