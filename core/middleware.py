from django.shortcuts import redirect
from django.conf import settings

# URLs, die ohne Login erreichbar sein sollen
OEFFENTLICHE_URLS = [
    '/login/',
]

class LoginErforderlichMiddleware:
    """
    Leitet alle nicht eingeloggten Besucher zur Login-Seite um.
    Ausnahme: die Login-Seite selbst.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if not any(request.path.startswith(url) for url in OEFFENTLICHE_URLS):
                return redirect(f'/login/?next={request.path}')
        return self.get_response(request)
