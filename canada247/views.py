from django.http import JsonResponse


def index(request):
    return JsonResponse(
        {
            "success": True,
            "message": "Canada 24/7 backend is running.",
            "data": {
                "name": "Canada 24/7 API",
                "health": "/api/health/",
                "admin": "/admin/",
            },
        }
    )


def health(request):
    return JsonResponse({"success": True, "message": "OK", "data": {"status": "healthy"}})
