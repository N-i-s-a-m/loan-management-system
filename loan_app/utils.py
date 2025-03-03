# File: utils.py
# Description: Utility functions for OTP generation, email sending, and admin access restriction.

import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from functools import wraps


def generate_otp():
    # Generate a random 6-digit OTP
    return str(random.randint(100000, 999999))


def send_otp_email(user):
    # Generate and send OTP to user's email
    otp = generate_otp()
    user.otp = otp  # Store OTP in the user model
    user.save()

    # Email details
    subject = "Your OTP for Email Verification"
    message = f"Your OTP for verifying your account is: {otp}"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])


def admin_required(view_func):
    # Decorator to restrict access to admin users only
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        # Check if user has admin role
        if request.user.role != "admin":
            return Response(
                {"detail": "Admin access required."},
                status=status.HTTP_403_FORBIDDEN
            )
        # Proceed with the view function if checks pass
        return view_func(self, request, *args, **kwargs)
    return wrapper