from django.http import JsonResponse


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
