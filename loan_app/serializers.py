# File: serializers.py
# Description: Defines serializers for User, Loan, and PaymentSchedule models to handle data serialization.

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Loan, PaymentSchedule

# Get the active user model
User = get_user_model()


# Serializer for User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'password']  # Fields to serialize
        extra_kwargs = {'password': {'write_only': True}}  # Ensure password is not exposed in responses

    def create(self, validated_data):
        # Create a new user with the validated data
        user = User.objects.create_user(**validated_data)
        return user


# Serializer for PaymentSchedule model
class PaymentScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentSchedule
        fields = [
            "installment_number", "due_date", "principal_component", 
            "interest_component", "remaining_balance", "status"
        ]  # Fields to serialize for payment schedule


# Serializer for Loan model
class LoanSerializer(serializers.ModelSerializer):
    # Nested serializer for payment schedule
    payment_schedule = PaymentScheduleSerializer(many=True, read_only=True, source="schedule")  # Links via related_name="schedule"
    amount_paid = serializers.SerializerMethodField()  # Custom field for calculated amount paid
    amount_remaining = serializers.SerializerMethodField()  # Custom field for calculated remaining amount
    user = serializers.SerializerMethodField()  # Custom field for user details

    class Meta:
        model = Loan
        fields = [
            "loan_id", "user", "amount", "tenure", "interest_rate", "monthly_installment",
            "total_interest", "total_payable", "status", "foreclosure_date", "foreclosure_discount",
            "final_settlement_amount", "created_at", "amount_paid", "amount_remaining", "payment_schedule"
        ]  # Fields to serialize for loan
        read_only_fields = [
            "loan_id", "monthly_installment", "total_interest", "total_payable", "created_at"
        ]  # Fields that cannot be modified via API

    def get_amount_paid(self, obj):
        # Calculate total amount paid based on paid installments
        paid_installments = obj.schedule.filter(status="PAID").count()
        return round(paid_installments * obj.monthly_installment, 2)

    def get_amount_remaining(self, obj):
        # Calculate remaining amount based on paid installments
        paid_installments = obj.schedule.filter(status="PAID").count()
        return round(obj.total_payable - (paid_installments * obj.monthly_installment), 2)

    def get_user(self, obj):
        # Return user details as a dictionary
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "email": obj.user.email
        }