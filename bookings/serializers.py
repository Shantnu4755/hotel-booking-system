from rest_framework import serializers
from .models import Room, Booking
from . import services 

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"


class BookingCreateSerializer(serializers.ModelSerializer):
    room_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Booking
        fields = [
            "room_id",
            "booking_type",
            "start_datetime",
            "end_datetime"
        ]

    def validate(self, attrs):
        # read room
        room_id = attrs.get("room_id")
        try:
            room = Room.objects.get(id=room_id, is_active=True)
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room not found!")
        attrs["room"] = room
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return services.create_booking(
            user=user,
            room=validated_data["room"],
            start=validated_data["start_datetime"],
            end=validated_data["end_datetime"],
            booking_type=validated_data["booking_type"],
        )


class BookingDetailSerializer(serializers.ModelSerializer):
    room = RoomSerializer()

    class Meta:
        model = Booking
        fields = "__all__"
