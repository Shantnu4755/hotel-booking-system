"""API views for the bookings app.

Refactored to use class-based views with GET and POST methods only,
using decorators for proper functionality.
"""

from __future__ import annotations

from django.utils import timezone
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import login, logout
from django.core.cache import cache
from django.utils import timezone
from .models import Booking, Room
from . import serializers as booking_serializers
from . import auth_serializers
from . import services


class IsOwner(permissions.BasePermission):
    """Allow access only to the owner of the booking."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# ==================== Room Views ====================

@method_decorator(csrf_exempt, name='dispatch')
class RoomListView(APIView):
    """List all active rooms - GET only."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get list of all active rooms."""
        rooms = Room.objects.filter(is_active=True).order_by("name")
        serializer = booking_serializers.RoomSerializer(rooms, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class RoomDetailView(APIView):
    """Get room details - GET only."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        """Get details of a specific room."""
        try:
            room = Room.objects.get(pk=pk, is_active=True)
        except Room.DoesNotExist:
            return Response(
                {"detail": "Room not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = booking_serializers.RoomSerializer(room)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class RoomAvailableView(APIView):
    """Search for available rooms - GET only."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return rooms available for the requested period.
        
        Query parameters:
        - start_datetime (ISO 8601)
        - end_datetime (ISO 8601)
        - booking_type (HOURLY or DAILY)
        """
        start_str = request.query_params.get("start_datetime")
        end_str = request.query_params.get("end_datetime")
        booking_type = request.query_params.get("booking_type")

        if not all([start_str, end_str, booking_type]):
            return Response(
                {"detail": "start_datetime, end_datetime and booking_type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start = timezone.datetime.fromisoformat(start_str)
            end = timezone.datetime.fromisoformat(end_str)
            if timezone.is_naive(start):
                start = timezone.make_aware(start, timezone.get_current_timezone())
            if timezone.is_naive(end):
                end = timezone.make_aware(end, timezone.get_current_timezone())
        except ValueError:
            return Response(
                {"detail": "Invalid datetime format. Use ISO 8601."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        availability_request = services.AvailabilityRequest(
            start=start,
            end=end,
            booking_type=booking_type,
        )

        rooms = services.search_available_rooms(availability_request)
        serializer = booking_serializers.RoomSerializer(rooms, many=True)
        return Response(serializer.data)


# ==================== Booking Views ====================

@method_decorator(csrf_exempt, name='dispatch')
class BookingListView(APIView):
    """List and create bookings - GET and POST."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of user's bookings."""
        bookings = (
            Booking.objects.select_related("room", "user")
            .filter(user=request.user)
            .order_by("-start_datetime")
        )
        serializer = booking_serializers.BookingDetailSerializer(bookings, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new booking."""
        serializer = booking_serializers.BookingCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        output_serializer = booking_serializers.BookingDetailSerializer(booking)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class BookingDetailView(APIView):
    """Get booking details - GET only."""
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        """Get booking object and check permissions."""
        try:
            booking = Booking.objects.select_related("room", "user").get(pk=pk)
        except Booking.DoesNotExist:
            return None
        
        # Check ownership
        if booking.user != self.request.user:
            return None
        
        return booking
    
    def get(self, request):
        bookings = (
            Booking.objects
            .select_related("room", "user")
            .filter(user=request.user)
            .order_by("-start_datetime")   # ✅ MOST RECENT FIRST
        )

        serializer = booking_serializers.BookingDetailSerializer(bookings, many=True)
        return Response(serializer.data)

@method_decorator(csrf_exempt, name='dispatch')
class BookingCheckInView(APIView):
    """Check-in a booking - POST only."""
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        """Get booking object and check permissions."""
        try:
            booking = Booking.objects.select_related("room", "user").get(pk=pk)
        except Booking.DoesNotExist:
            return None
        
        if booking.user != self.request.user:
            return None
        
        return booking
    
    def post(self, request, pk):
        """Check-in a booking."""
        booking = self.get_object(pk)
        if not booking:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            services.check_in(booking)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = booking_serializers.BookingDetailSerializer(booking)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class BookingCheckOutView(APIView):
    """Check-out a booking - POST only."""
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        """Get booking object and check permissions."""
        try:
            booking = Booking.objects.select_related("room", "user").get(pk=pk)
        except Booking.DoesNotExist:
            return None
        
        if booking.user != self.request.user:
            return None
        
        return booking
    
    def post(self, request, pk):
        """Check-out a booking."""
        booking = self.get_object(pk)
        if not booking:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            services.check_out(booking)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = booking_serializers.BookingDetailSerializer(booking)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class BookingCancelView(APIView):
    """Cancel a booking - POST only."""
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        """Get booking object and check permissions."""
        try:
            booking = Booking.objects.select_related("room", "user").get(pk=pk)
        except Booking.DoesNotExist:
            return None
        
        if booking.user != self.request.user:
            return None
        
        return booking
    
    def post(self, request, pk):
        """Cancel a booking."""
        booking = self.get_object(pk)
        if not booking:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            services.cancel_booking(booking)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = booking_serializers.BookingDetailSerializer(booking)
        return Response(serializer.data)


# ==================== Authentication Views ====================

@method_decorator(csrf_exempt, name='dispatch')
class SignupView(APIView):
    """User signup - POST only."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Create a new user account."""
        serializer = auth_serializers.SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Auto-login after signup
        login(request, user)
        
        # Cache user session info
        cache_key = f"user_session_{user.id}"
        cache.set(cache_key, {
            'username': user.username,
            'email': user.email,
            'logged_in_at': timezone.now().isoformat()
        }, timeout=86400)  # 24 hours
        
        user_data = auth_serializers.UserSerializer(user).data
        return Response({
            'message': 'User created successfully',
            'user': user_data
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """User login - POST only."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Authenticate user and create session."""
        serializer = auth_serializers.LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Create session
        login(request, user)
        
        # Cache user session info
        cache_key = f"user_session_{user.id}"
        cache.set(cache_key, {
            'username': user.username,
            'email': user.email,
            'logged_in_at': timezone.now().isoformat()
        }, timeout=86400)  # 24 hours
        
        user_data = auth_serializers.UserSerializer(user).data
        return Response({
            'message': 'Login successful',
            'user': user_data
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """User logout - POST only."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Logout user and clear session cache."""
        user_id = request.user.id
        
        # Clear cache
        cache_key = f"user_session_{user_id}"
        cache.delete(cache_key)
        
        # Logout
        logout(request)
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class UserProfileView(APIView):
    """Get current user profile - GET only."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user information."""
        # Check cache first
        cache_key = f"user_session_{request.user.id}"
        cached_data = cache.get(cache_key)
        
        user_data = auth_serializers.UserSerializer(request.user).data
        
        if cached_data:
            user_data['cached_session'] = cached_data
        
        return Response(user_data)


# ==================== Frontend View ====================

def frontend_view(request):
    """Serve the frontend HTML file."""
    return render(request, 'frontend.html')
