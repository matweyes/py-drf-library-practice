from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from user.views import CreateUserView, ManageUserView

app_name = "user"

decorated_token_obtain = extend_schema(
    tags=["Users"],
    description="Obtain a JWT access + refresh token pair using email and password.",
)(TokenObtainPairView)

decorated_token_refresh = extend_schema(
    tags=["Users"],
    description="Refresh an expired access token using a valid refresh token.",
)(TokenRefreshView)

urlpatterns = [
    path("", CreateUserView.as_view(), name="create"),
    path("token/", decorated_token_obtain.as_view(), name="token_obtain_pair"),
    path("token/refresh/", decorated_token_refresh.as_view(), name="token_refresh"),
    path("me/", ManageUserView.as_view(), name="manage"),
]
