from django.http import HttpResponseRedirect


class LoginRequiredMiddleware:
    """Redirect anonymous users to the login page for non-exempt paths.

    Exempt paths include the auth endpoints, admin and static files.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info or ''

        # Paths that do not require authentication
        exempt_prefixes = ('/users', '/admin')

        if not request.user.is_authenticated:
            if not any(path.startswith(prefix) for prefix in exempt_prefixes):
                return HttpResponseRedirect(f'/users/login')

        return self.get_response(request)
