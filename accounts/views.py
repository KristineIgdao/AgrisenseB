from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import PasswordResetOTP
from .serializers import SensorReadingSerializer, DailySummarySerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@csrf_exempt
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'detail': 'Invalid credentials'}, status=401)

    login(request, user)

    # ✅ Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        'message': 'Login successful',
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'token': access_token,
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def register_user(request):
    data = request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=400)

    if email and User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'}, status=400)

    user = User.objects.create_user(
        username=username,
        email=email or "",
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    return Response({'message': 'User registered successfully.'}, status=201)



# ✅ SEND RESET OTP
@api_view(['POST'])
def send_reset_otp(request):
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required.'}, status=400)

    try:
        user = User.objects.get(email=email)
        otp = get_random_string(length=6, allowed_chars='0123456789')
        PasswordResetOTP.objects.update_or_create(user=user, defaults={'otp': otp})

        send_mail(
            'AgriSense Password Reset OTP',
            f'Your OTP for password reset is: {otp}',
            'noreply@agrisense.com',
            [email],
            fail_silently=False,
        )
        return Response({'message': 'OTP sent to your email.'}, status=200)

    except User.DoesNotExist:
        return Response({'message': 'Email not found.'}, status=404)


# ✅ VERIFY OTP
@api_view(['POST'])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    if not email or not otp:
        return Response({'message': 'Email and OTP are required.'}, status=400)

    try:
        user = User.objects.get(email=email)
        record = PasswordResetOTP.objects.get(user=user)
        if record.otp == otp:
            return Response({'message': 'OTP verified.'}, status=200)
        return Response({'message': 'Invalid OTP.'}, status=400)
    except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
        return Response({'message': 'Invalid request.'}, status=400)


# ✅ RESET PASSWORD
@api_view(['POST'])
def reset_password(request):
    email = request.data.get('email')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not email or not new_password or not confirm_password:
        return Response({'message': 'All fields are required.'}, status=400)

    if new_password != confirm_password:
        return Response({'message': 'Passwords do not match.'}, status=400)

    try:
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        PasswordResetOTP.objects.filter(user=user).delete()
        return Response({'message': 'Password reset successful.'}, status=200)
    except User.DoesNotExist:
        return Response({'message': 'User not found.'}, status=404)


# ✅ STORE SENSOR READING
@api_view(['POST'])
def store_sensor_reading(request):
    serializer = SensorReadingSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ STORE DAILY SUMMARY
@api_view(['POST'])
def store_daily_summary(request):
    serializer = DailySummarySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


