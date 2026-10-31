from decimal import Decimal, InvalidOperation

from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from .models import HuntLog, WantedCriminal
from .serializers import HuntLogSerializer, WantedCriminalSerializer

TRUE_VALUES = {"true", "1", "yes"}
FALSE_VALUES = {"false", "0", "no"}


def parse_bool(name, raw):
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ValidationError({name: f"'{raw}' is not a valid boolean. Use true or false."})


def parse_decimal(name, raw):
    try:
        return Decimal(raw)
    except InvalidOperation:
        raise ValidationError({name: f"'{raw}' is not a valid number."})


class WantedCriminalViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/criminals/ (с фильтрами и сортировкой) и GET /api/criminals/{id}/"""

    queryset = WantedCriminal.objects.all()
    serializer_class = WantedCriminalSerializer
    pagination_class = None  # простой список без обёртки

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            return qs
        p = self.request.query_params

        # Все фильтры накладываются друг на друга, поэтому работают вместе
        if p.get("min_reward"):
            qs = qs.filter(reward__gte=parse_decimal("min_reward", p["min_reward"]))
        if p.get("max_reward"):
            qs = qs.filter(reward__lte=parse_decimal("max_reward", p["max_reward"]))
        for flag in ("armed", "has_crew", "escape_master"):
            if p.get(flag):
                qs = qs.filter(**{flag: parse_bool(flag, p[flag])})

        sort = p.get("sort")
        if sort:
            if sort not in ("reward", "-reward"):
                raise ValidationError({"sort": "Allowed values: reward, -reward."})
            qs = qs.order_by(sort, "id")
        return qs


class HuntLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD журнала охоты. Обновление только через PATCH (success, notes)."""

    queryset = HuntLog.objects.select_related("criminal").all()
    serializer_class = HuntLogSerializer
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        raw = self.request.query_params.get("criminal_id")
        if raw:
            if not raw.isdigit():
                raise ValidationError({"criminal_id": f"'{raw}' is not a valid id."})
            qs = qs.filter(criminal_id=int(raw))
        return qs
