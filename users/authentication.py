import requests
from jose import jwt, JWTError, ExpiredSignatureError
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import UserProfile


class SupabaseAuthentication(BaseAuthentication):
    """
    Placeholder for Supabase JWT authentication logic.
    This will be implemented in the future to verify tokens issued by Supabase Auth.
    """

    _jwks_cache = None  # cached per process — avoids network call on every request

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None  # no token — let permission classes handle it
        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return None

        claims = self._verify_token(token)
        user = self._get_or_create_user(claims)
        return (user, token)

    def authenticate_header(self, request):
        return "Bearer"

    def _verify_token(self, token):
        try:
            jwks = self._get_jwks()
            claims = jwt.decode(
                token,
                jwks,
                algorithms=["RS256", "ES256"],
                options={
                    "verify_aud": False,  # Supabase tokens don't have an aud claim
                },
            )
        except ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired.")
        except JWTError as e:
            raise AuthenticationFailed(f"Invalid token: {e}")
        except Exception as e:
            raise AuthenticationFailed(f"Token verification failed: {e}")
        return claims

    def _get_or_create_user(self, claims):
        supabase_uid = claims.get("sub")
        if not supabase_uid:
            raise AuthenticationFailed("Token missing sub claim.")

        email = claims.get("email", "")

        # Supabase stores name fields inside user_metadata
        user_metadata = claims.get("user_metadata", {})
        given_name = user_metadata.get("first_name", "")
        family_name = user_metadata.get("last_name", "")

        user, _ = UserProfile.get_or_create_from_supabase(
            supabase_uid=supabase_uid,
            email=email,
            given_name=given_name,
            family_name=family_name,
        )
        return user

    def _get_jwks(self):
        """
        Fetch Supabase's public JWKS and cache per process.
        Same pattern as Cognito — public keys used to verify JWT signature.
        """
        if SupabaseAuthentication._jwks_cache is None:
            try:
                response = requests.get(settings.SUPABASE_JWKS_URL, timeout=5)
                response.raise_for_status()
                SupabaseAuthentication._jwks_cache = response.json()
            except requests.RequestException as e:
                raise AuthenticationFailed(f"Could not fetch Supabase public keys: {e}")
        return SupabaseAuthentication._jwks_cache


# import requests
# from jose import jwt, JWTError, ExpiredSignatureError
# from django.conf import settings
# from rest_framework.authentication import BaseAuthentication
# from rest_framework.exceptions import AuthenticationFailed

# from .models import UserProfile


# class CognitoAuthentication(BaseAuthentication):
#     """
#     Verifies AWS Cognito JWT tokens sent as:
#         Authorization: Bearer <token>

#     On success: sets request.user to a UserProfile instance.
#     On failure: raises AuthenticationFailed.
#     No token present: returns None (allows public endpoints to work).
#     """

#     _jwks_cache = None  # cached per process — avoids network call on every request

#     def authenticate(self, request):
#         auth_header = request.headers.get("Authorization", "")

#         if not auth_header.startswith("Bearer "):
#             return None  # no token — let permission classes handle it

#         token = auth_header.split(" ", 1)[1].strip()

#         if not token:
#             return None

#         claims = self._verify_token(token)
#         user = self._get_or_create_user(claims)
#         return (user, token)

#     def authenticate_header(self, request):
#         # tells DRF to return WWW-Authenticate: Bearer on 401 responses
#         return "Bearer"

#     # ------------------------------------------------------------------
#     # Private methods
#     # ------------------------------------------------------------------

#     def _verify_token(self, token):
#         try:
#             jwks = self._get_jwks()
#             claims = jwt.decode(
#                 token,
#                 jwks,
#                 algorithms=["RS256"],
#                 audience=settings.AWS_COGNITO_APP_CLIENT_ID,
#                 options={"verify_at_hash": False},
#             )
#         except ExpiredSignatureError:
#             raise AuthenticationFailed("Token has expired.")
#         except JWTError as e:
#             raise AuthenticationFailed(f"Invalid token: {e}")
#         except Exception as e:
#             raise AuthenticationFailed(f"Token verification failed: {e}")

#         # verify the token was issued by our specific user pool
#         expected_issuer = (
#             f"https://cognito-idp.{settings.AWS_COGNITO_REGION}.amazonaws.com/"
#             f"{settings.AWS_COGNITO_USER_POOL_ID}"
#         )
#         if claims.get("iss") != expected_issuer:
#             raise AuthenticationFailed("Token issuer is invalid.")

#         # token_use must be id or access — reject anything else
#         if claims.get("token_use") not in ("id", "access"):
#             raise AuthenticationFailed("Invalid token_use claim.")

#         return claims

#     def _get_or_create_user(self, claims):
#         cognito_sub = claims.get("sub")
#         if not cognito_sub:
#             raise AuthenticationFailed("Token missing sub claim.")

#         # these fields are only in id tokens, not access tokens
#         email = claims.get("email", "")
#         given_name = claims.get("given_name", "")
#         family_name = claims.get("family_name", "")

#         user, _ = UserProfile.get_or_create_from_cognito(
#             cognito_sub=cognito_sub,
#             email=email,
#             given_name=given_name,
#             family_name=family_name,
#         )
#         return user

#     def _get_jwks(self):
#         """
#         Fetch Cognito's public keys and cache them.
#         These keys are used to verify the JWT signature.
#         They rarely change so caching per process is safe.
#         """
#         if CognitoAuthentication._jwks_cache is None:
#             try:
#                 response = requests.get(settings.AWS_COGNITO_JWKS_URL, timeout=5)
#                 response.raise_for_status()
#                 CognitoAuthentication._jwks_cache = response.json()
#             except requests.RequestException as e:
#                 raise AuthenticationFailed(f"Could not fetch Cognito public keys: {e}")
#         return CognitoAuthentication._jwks_cache
