# File: authentication.py
# Description: Custom JWT authentication class for validating user tokens in API requests.

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

# Get the active user model
User = get_user_model()


# Custom JWT Authentication class
class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Retrieve the Authorization header from the request
        auth_header = request.headers.get("Authorization")

        # Check if the header exists and starts with "Bearer "
        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # No credentials provided, let other authentication handle it

        # Extract the token from the header
        token = auth_header.split(" ")[1]

        try:
            # Validate the token and retrieve user ID
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            # Fetch the user from the database
            user = User.objects.get(id=user_id)
        except Exception:
            # Raise an error if token is invalid or expired
            raise AuthenticationFailed("Invalid or expired token")

        # Return the authenticated user and token (None for token since it's handled by JWT)
        return (user, None)