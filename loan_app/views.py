# File: views.py
# Description: Contains API views and HTML page rendering functions for user, loan, and admin operations.

from rest_framework.generics import CreateAPIView, ListCreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta, datetime
from .serializers import UserSerializer, LoanSerializer
from decimal import Decimal
from .models import User, Loan, PaymentSchedule
from .utils import send_otp_email, admin_required
import jwt
import math
from .permissions import IsAdminUser, IsUser

# Get the active user model
User = get_user_model()


# Admin home page view
def admin_home(request):
    return render(request, "Admin/admin_home.html")


# Admin view to list all loans
class AdminLoanListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            # Restrict access to staff users only
            if not request.user.is_staff:
                return Response(
                    {"success": False, "message": "Access Denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Fetch all loans and serialize them
            loans = Loan.objects.all()
            serializer = LoanSerializer(loans, many=True)
            return Response(
                {"success": True, "loans": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Admin view to delete a loan and its payment schedule
class AdminDeleteLoanView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, loan_id):
        try:
            # Fetch the loan by loan_id
            loan = Loan.objects.get(loan_id=loan_id)

            # Capture loan details before deletion
            deleted_loan_data = {
                "loan_id": loan.loan_id,
                "amount": loan.amount,
                "tenure": loan.tenure,
                "monthly_installment": loan.monthly_installment,
                "total_interest": loan.total_interest,
                "status": loan.status,
                "created_at": loan.created_at,
            }

            # Delete associated payment schedules first
            PaymentSchedule.objects.filter(loan=loan).delete()
            # Delete the loan
            loan.delete()

            return Response({
                "success": True,
                "message": "Loan and its payment schedule deleted successfully.",
                "deleted_loan": deleted_loan_data
            }, status=status.HTTP_200_OK)

        except Loan.DoesNotExist:
            return Response(
                {"success": False, "message": "Loan not found."},
                status=status.HTTP_404_NOT_FOUND
            )


# Custom JWT authentication override
class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError):
            # Silently handle invalid/expired tokens
            return None


# User registration view
class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Validation failed", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Extract role from request data (default to "user")
            role = request.data.get("role", "user").lower()
            is_admin = role == "admin"

            # Create user with specified role and admin privileges
            user = serializer.save(
                is_verified=False,
                role=role,
                is_staff=is_admin,
                is_superuser=is_admin
            )

            # Send OTP for email verification
            send_otp_email(user)

            return Response(
                {"success": True, "message": "Registration successful. Check your email for OTP verification."},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Registration failed", "errors": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# OTP verification view
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = User.objects.get(email=email)
            if user.otp == otp:
                user.is_verified = True
                user.otp = None  # Clear OTP after verification
                user.save()
                return JsonResponse({"message": "Email verified successfully!"}, status=200)
            else:
                return JsonResponse({"error": "Invalid OTP!"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found!"}, status=400)


# User login view
class UserLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate the user
        user = authenticate(email=email, password=password)
        if not user:
            return Response(
                {"success": False, "detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email is verified
        if not user.is_verified:
            return Response(
                {"detail": "Email not verified. Please verify before logging in."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)


# HTML page rendering views
def login_page(request):
    return render(request, "Guest/login.html")


def register_page(request):
    return render(request, "Guest/register.html")


def user_home(request):
    return render(request, "User/home.html")


def guest_page(request):
    return render(request, "Guest/guestPage.html")


def loan_application_page(request):
    return render(request, "User/loan_application.html")


# User info view
class UserInfoView(APIView):
    permission_classes = [IsAuthenticated, IsUser]

    def get(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            return Response({"user_id": user_id})
        return Response({"error": "Not logged in"}, status=401)


# Logout view
class LogoutView(APIView):
    def post(self, request):
        request.session.flush()  # Clear server-side session
        response = Response({"success": True, "message": "Logged out"})
        response.delete_cookie('access_token')  # Clear access token cookie if used
        return response


# Loan management view
class LoanView(APIView):
    permission_classes = [IsAuthenticated, IsUser]

    def get(self, request):
        # Fetch loans for the authenticated user
        loans = Loan.objects.filter(user=request.user).values(
            "loan_id", "amount", "tenure", "monthly_installment", 
            "total_payable", "amount_paid", "amount_remaining", 
            "next_due_date", "status", "created_at"
        )

        response_data = {
            "status": "success",
            "data": {"loans": list(loans)}
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            user = request.user
            amount = int(request.data.get("amount"))
            tenure = int(request.data.get("tenure"))
            interest_rate = int(request.data.get("interest_rate"))

            # Calculate EMI
            monthly_interest_rate = (interest_rate / 100) / 12
            emi = (amount * monthly_interest_rate * (math.pow(1 + monthly_interest_rate, tenure))) / \
                  ((math.pow(1 + monthly_interest_rate, tenure)) - 1)

            # Calculate total interest and payable amount
            interest_amount_after_all_emi = emi * tenure - amount
            interest_total = amount * (interest_rate / 100)
            total_interest = interest_total + interest_amount_after_all_emi
            total_amount = amount + total_interest

            # Create loan object
            loan = Loan.objects.create(
                user=user,
                amount=amount,
                tenure=tenure,
                interest_rate=interest_rate,
                monthly_installment=round(emi, 2),
                total_interest=round(total_interest, 2),
                total_payable=round(total_amount, 2),
                status="ACTIVE"
            )

            # Generate payment schedule
            self.generate_payment_schedule(loan)

            # Fetch payment schedule
            schedule = PaymentSchedule.objects.filter(loan=loan).order_by("installment_number")
            payment_schedule = [
                {
                    "installment_no": entry.installment_number,
                    "due_date": entry.due_date.strftime("%Y-%m-%d"),
                    "amount": float(entry.principal_component + entry.interest_component)
                }
                for entry in schedule
            ]

            return Response({
                "status": "success",
                "data": {
                    "loan_id": loan.loan_id,
                    "amount": loan.amount,
                    "tenure": loan.tenure,
                    "interest_rate": f"{loan.interest_rate}% yearly",
                    "monthly_installment": round(emi, 2),
                    "total_interest": round(total_interest, 2),
                    "total_amount": round(total_amount, 2),
                    "payment_schedule": payment_schedule,
                    "status": loan.status,
                    "created_at": loan.created_at
                }
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def generate_payment_schedule(self, loan):
        # Generate payment schedule for the loan
        balance = Decimal(loan.amount)
        emi = Decimal(loan.monthly_installment)
        interest_rate = Decimal(loan.interest_rate) / 12 / 100
        start_date = now().date()

        schedule_entries = []
        for i in range(1, loan.tenure + 1):
            interest_component = balance * interest_rate
            principal_component = emi - interest_component
            balance -= principal_component

            schedule_entries.append(PaymentSchedule(
                loan=loan,
                installment_number=i,
                due_date=start_date + relativedelta(months=i),
                principal_component=round(principal_component, 2),
                interest_component=round(interest_component, 2),
                remaining_balance=round(balance, 2),
            ))

        PaymentSchedule.objects.bulk_create(schedule_entries)


# Loan list view
@permission_classes([IsAuthenticated, IsUser])
def loan_list_view(request):
    loans = Loan.objects.filter(user_id=request.GET.get("user_id"))
    return render(request, "User/loan_list.html", {"loans": loans})


# Loan details view
@permission_classes([IsAuthenticated, IsUser])
def loan_details_view(request):
    loan_id = request.GET.get("loan_id")
    loan = get_object_or_404(Loan, loan_id=loan_id)

    payment_schedule = PaymentSchedule.objects.filter(loan=loan).order_by("installment_number")
    pending_payment = payment_schedule.filter(status="PENDING").first()
    balance_amount = pending_payment.remaining_balance if pending_payment else 0

    context = {
        "loan": loan,
        "payment_schedule": payment_schedule,
        "balance_amount": balance_amount,
    }
    return render(request, "User/loan_details.html", context)


# Pay installment API
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
def pay_installment(request):
    payment_id = request.data.get('payment_id')
    if not payment_id:
        return Response({"error": "Payment ID not provided."}, status=400)

    try:
        payment = PaymentSchedule.objects.get(pk=payment_id)
    except PaymentSchedule.DoesNotExist:
        return Response({"error": "Payment not found."}, status=404)

    if payment.status != "PENDING":
        return Response({"error": "Payment already made."}, status=400)

    payment.status = "PAID"
    payment.save()

    loan = payment.loan
    if loan.amount_paid is None:
        loan.amount_paid = 0
    loan.amount_paid += loan.monthly_installment
    loan.amount_remaining = loan.amount - loan.amount_paid
    next_payment = loan.schedule.filter(status="PENDING").order_by("installment_number").first()

    if next_payment:
        loan.next_due_date = next_payment.due_date
    else:
        loan.next_due_date = None
        loan.status = "CLOSED"

    loan.save()
    return Response({"success": True})


# Foreclose loan view
class ForecloseLoanView(APIView):
    permission_classes = [IsAuthenticated, IsUser]

    def post(self, request, loan_id):
        try:
            loan = Loan.objects.filter(user=request.user, loan_id=loan_id, status="ACTIVE").first()
            if not loan:
                return Response({"error": "Loan not found or already closed"}, status=400)

            paid_installments = PaymentSchedule.objects.filter(loan=loan, due_date__lte=now().date())
            total_paid = sum([entry.principal_component + entry.interest_component for entry in paid_installments])

            # Calculate remaining balance and foreclosure details
            remaining_balance = loan.total_payable - total_paid
            remaining_interest = loan.total_interest - sum([entry.interest_component for entry in paid_installments])
            foreclosure_discount = remaining_interest * Decimal("0.05")
            final_settlement_amount = remaining_balance - foreclosure_discount

            # Update loan details
            loan.status = "CLOSED"
            loan.final_settlement_amount = round(final_settlement_amount, 2)
            loan.foreclosure_discount = round(foreclosure_discount, 2)
            loan.foreclosure_date = now().date()
            loan.save()

            # Mark all payment schedules as paid
            PaymentSchedule.objects.filter(loan=loan).update(status="PAID")

            return Response({
                "success": "success",
                "message": "Loan foreclosed successfully!",
                "loan_id": loan.loan_id,
                "foreclosure_discount": round(foreclosure_discount, 2),
                "final_settlement_amount": round(final_settlement_amount, 2),
                "foreclosure_date": loan.foreclosure_date,
                "status": loan.status
            }, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


# Foreclosure details API
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsUser])
def foreclosure_details(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    total_paid = loan.amount_paid if loan.amount_paid else Decimal("0")

    # Calculate remaining balance
    if total_paid == Decimal("0"):
        remaining_balance = loan.amount
    else:
        remaining_balance = loan.amount_remaining if loan.amount_remaining is not None else (loan.amount - total_paid)

    # Calculate foreclosure discount and final settlement amount
    foreclosure_discount = Decimal("0.05") * remaining_balance
    final_settlement_amount = remaining_balance - foreclosure_discount

    return Response({
        "total_paid": total_paid,
        "remaining_balance": remaining_balance,
        "foreclosure_discount": foreclosure_discount,
        "final_settlement_amount": final_settlement_amount,
    })