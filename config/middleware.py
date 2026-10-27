from django.http import JsonResponse
from django.utils.cache import add_never_cache_headers


class EarlyHealthCheckMiddleware:
    """
    Answer /health/ before CommonMiddleware validates Host.
    Railway health probes may use Host headers that are not in ALLOWED_HOSTS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in ("/health", "/health/"):
            return JsonResponse({"status": "ok"})
        return self.get_response(request)


class NoStoreHTMLMiddleware:
    """Keep rendered forms out of the browser's back/forward cache.

    Django rotates the CSRF token when a user signs in. Reusing a previously
    rendered form from the browser cache then submits a token that no longer
    matches the CSRF cookie and results in a 403. Dynamic HTML should therefore
    always be fetched again before it is submitted.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.headers.get("Content-Type", "")
        if request.method == "GET" and content_type.startswith("text/html"):
            add_never_cache_headers(response)
        return response
