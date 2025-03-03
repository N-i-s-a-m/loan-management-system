# File: urls.py
# Description: Defines URL patterns for API endpoints and HTML page views in the project.

from django.urls import path
from .views import (
    RegisterUserView, VerifyOTPView, UserLoginView, login_page, register_page, 
    user_home, guest_page, UserInfoView, LogoutView, 
    loan_application_page, loan_list_view, loan_details_view, pay_installment, 
    ForecloseLoanView, LoanView, foreclosure_details, AdminLoanListView, AdminDeleteLoanView, admin_home
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# URL patterns
urlpatterns = [
    # Authentication token endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Generate JWT token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh JWT token

    # User authentication API endpoints
    path("api/register/", RegisterUserView.as_view(), name="register"),  # User registration
    path("api/verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),  # OTP verification
    path("api/login/", UserLoginView.as_view(), name="login"),  # User login
    path('api/user-info/', UserInfoView.as_view(), name='user_info'),  # Retrieve user information
    path('api/logout/', LogoutView.as_view(), name='logout'),  # User logout

    # Loan-related API endpoints
    path('api/loans/', LoanView.as_view(), name='list_loan'),  # List loans (GET only)
    path('api/payment_schedule/pay/', pay_installment, name='pay_installment'),  # Pay loan installment
    path('api/loans/<str:loan_id>/foreclose/', ForecloseLoanView.as_view(), name='foreclose-loan'),  # Foreclose a loan
    path('api/loans/<str:loan_id>/foreclosure-details/', foreclosure_details, name='foreclosure_details'),  # Get foreclosure details

    # Loan-related HTML views
    path("loan_list/", loan_list_view, name='loan_list'),  # Display list of loans
    path('loan_details/', loan_details_view, name='loan_details'),  # Display loan details

    # HTML page views
    path("register/", register_page, name="register_page"),  # User registration page
    path("login/", login_page, name="login_page"),  # User login page
    path("user_home/", user_home, name="user_home"),  # User dashboard
    path("loan_app/", guest_page, name="guest_page"),  # Guest loan application page
    path("apply_loan_page/", loan_application_page, name="apply_loan_page"),  # Loan application page

    # Admin-related endpoints and views
    path("admin_home/", admin_home, name="admin_home"),  # Admin dashboard
    path("api/admin/loans/", AdminLoanListView.as_view(), name="admin-loans-api"),  # List all loans for admin
    path('api/admin/loans/<str:loan_id>/delete/', AdminDeleteLoanView.as_view(), name='delete-loan'),  # Delete a loan
]