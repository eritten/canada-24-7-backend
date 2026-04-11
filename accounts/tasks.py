from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task
def send_otp_email_task(email, otp_code, subject):
    html_content = render_to_string(
        "emails/otp_email.html",
        {"otp_code": otp_code, "app_name": "Canada 24/7", "frontend_url": settings.FRONTEND_URL},
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=f"Your Canada 24/7 OTP code is {otp_code}. It expires in 10 minutes.",
        to=[email],
    )
    message.attach_alternative(html_content, "text/html")
    message.send()
