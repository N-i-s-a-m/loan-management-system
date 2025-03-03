# File: models.py
# Description: Defines the custom user model, loan, and payment schedule models for the project.

import uuid
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now

# Custom User Model
class CustomUser(AbstractUser):
    # Choices for user roles
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    
    # User fields
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')  # User role (admin/user)
    email = models.EmailField(unique=True)  # Unique email as username
    is_verified = models.BooleanField(default=False)  # Tracks email verification status
    otp = models.CharField(max_length=6, blank=True, null=True)  # Stores OTP for verification
    is_staff = models.BooleanField(default=False)  # Grants access to admin panel
    is_superuser = models.BooleanField(default=False)  # Grants all permissions

    # Authentication configuration
    USERNAME_FIELD = 'email'  # Use email for login instead of username
    REQUIRED_FIELDS = ['username']  # Username is still required

    def __str__(self):
        return f"{self.email} ({self.role})"  # String representation of the user


# Get the active user model
User = get_user_model()


# Loan Model
class Loan(models.Model):
    # Loan fields
    loan_id = models.CharField(max_length=10, unique=True, editable=False)  # Unique loan identifier
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Associated user
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Loan amount
    tenure = models.IntegerField()  # Loan duration in months
    interest_rate = models.FloatField()  # Interest rate percentage
    monthly_installment = models.DecimalField(max_digits=10, decimal_places=2)  # Monthly EMI
    total_interest = models.DecimalField(max_digits=10, decimal_places=2)  # Total interest payable
    total_payable = models.DecimalField(max_digits=10, decimal_places=2)  # Total amount to be paid
    status = models.CharField(
        max_length=20, 
        choices=[('ACTIVE', 'Active'), ('CLOSED', 'Closed')], 
        default='ACTIVE'
    )  # Loan status
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Amount paid so far
    amount_remaining = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Remaining balance
    next_due_date = models.DateField(null=True, blank=True)  # Next payment due date
    foreclosure_date = models.DateField(null=True, blank=True)  # Date of foreclosure, if applicable
    foreclosure_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Discount on foreclosure
    final_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Final settlement amount
    created_at = models.DateTimeField(auto_now_add=True)  # Loan creation timestamp
    
    def save(self, *args, **kwargs):
        # Generate unique loan_id if not already set
        if not self.loan_id:
            last_loan = Loan.objects.order_by("-id").first()
            if last_loan and last_loan.loan_id.startswith("LOAN"):
                last_number = int(last_loan.loan_id.replace("LOAN", ""))
                self.loan_id = f"LOAN{last_number + 1:03}"  # Incremental ID (e.g., LOAN002)
            else:
                self.loan_id = "LOAN001"  # Default ID for first loan
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan_id} - {self.user.email}"  # String representation of the loan


# Payment Schedule Model
class PaymentSchedule(models.Model):
    # Payment schedule fields
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="schedule", to_field="loan_id")  # Linked loan
    installment_number = models.IntegerField()  # Installment sequence number
    due_date = models.DateField()  # Due date for this installment
    principal_component = models.DecimalField(max_digits=10, decimal_places=2)  # Principal portion of payment
    interest_component = models.DecimalField(max_digits=10, decimal_places=2)  # Interest portion of payment
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)  # Remaining loan balance
    status = models.CharField(
        max_length=20, 
        choices=[('PENDING', 'Pending'), ('PAID', 'Paid')], 
        default='PENDING'
    )  # Payment status