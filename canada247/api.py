from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def sanitize_text(value):
    return strip_tags(value).strip() if isinstance(value, str) else value


def success_response(message="Success", data=None, status_code=status.HTTP_200_OK):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)


def paginated_response(data, message="Success"):
    return Response({"success": True, "message": message, "data": data}, status=status.HTTP_200_OK)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"success": False, "message": "An unexpected error occurred.", "errors": {"detail": [str(exc)]}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message = "Request failed."
    if isinstance(response.data, dict) and response.data.get("detail"):
        message = str(response.data.get("detail"))
    response.data = {"success": False, "message": message, "errors": response.data}
    return response
