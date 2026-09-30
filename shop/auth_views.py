from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ValidationError
from .security import LoginThrottle, RegisterThrottle, RefreshThrottle
from .serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'id': user.pk, 'username': user.username}, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]


class RefreshView(TokenRefreshView):
    throttle_classes = [RefreshThrottle]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [RefreshThrottle]

    def post(self, request):
        class Input(serializers.Serializer):
            refresh = serializers.CharField(max_length=4096)
        data = Input(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            token = RefreshToken(data.validated_data['refresh'])
            if str(token['user_id']) != str(request.user.pk):
                raise ValidationError({'refresh': 'El token no corresponde a tu cuenta.'})
            token.blacklist()
        except TokenError:
            raise ValidationError({'refresh': 'Token de renovación inválido o revocado.'})
        return Response(status=status.HTTP_204_NO_CONTENT)
