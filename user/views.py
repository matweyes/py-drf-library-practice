from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.serializers import UserSerializer


@extend_schema(
    tags=["Users"],
    description="Register a new user with email and password.",
)
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


@extend_schema_view(
    get=extend_schema(description="Retrieve the authenticated user's profile."),
    put=extend_schema(description="Fully update the authenticated user's profile."),
    patch=extend_schema(description="Partially update the authenticated user's profile."),
)
@extend_schema(tags=["Users"])
class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
