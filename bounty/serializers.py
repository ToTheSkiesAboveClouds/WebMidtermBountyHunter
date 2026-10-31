from rest_framework import serializers

from .models import HuntLog, WantedCriminal


class WantedCriminalSerializer(serializers.ModelSerializer):
    # Координаты одним объектом для удобства; null, если координат нет
    last_known_coordinates = serializers.SerializerMethodField()

    class Meta:
        model = WantedCriminal
        fields = [
            "id", "name", "nickname", "reward",
            "latitude", "longitude", "location_note", "last_known_coordinates",
            "difficulty", "armed", "has_crew", "escape_master",
        ]

    def get_last_known_coordinates(self, obj):
        if obj.latitude is None or obj.longitude is None:
            return None
        return {"latitude": obj.latitude, "longitude": obj.longitude}


class HuntLogSerializer(serializers.ModelSerializer):
    # Клиент передаёт criminal_id, внутри это связь criminal
    criminal_id = serializers.PrimaryKeyRelatedField(
        source="criminal", queryset=WantedCriminal.objects.all()
    )

    class Meta:
        model = HuntLog
        fields = ["id", "criminal_id", "success", "notes", "created_at"]
        read_only_fields = ["created_at"]  # время ставит сервер, из запроса игнорируется

    def validate_notes(self, value):
        if not value.strip():
            raise serializers.ValidationError("Notes must not be blank.")
        return value

    def validate(self, attrs):
        # При обновлении можно менять только success и notes
        if self.instance and "criminal" in attrs and attrs["criminal"] != self.instance.criminal:
            raise serializers.ValidationError(
                {"criminal_id": "Criminal of an existing hunt log cannot be changed."}
            )
        return attrs
