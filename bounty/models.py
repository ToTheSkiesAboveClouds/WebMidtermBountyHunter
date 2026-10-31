from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class WantedCriminal(models.Model):
    name = models.CharField(max_length=120, blank=True, null=True)  # настоящее имя, может быть неизвестно
    nickname = models.CharField(max_length=120)
    reward = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    # Последнее известное местоположение: либо координаты, либо текстовая заметка (либо и то и другое)
    latitude = models.FloatField(
        blank=True, null=True, validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        blank=True, null=True, validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    location_note = models.TextField(blank=True, default="")

    difficulty = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    armed = models.BooleanField(default=False)
    has_crew = models.BooleanField(default=False)
    escape_master = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(difficulty__gte=1, difficulty__lte=10),
                name="criminal_difficulty_1_10",
            )
        ]

    def __str__(self):
        return f"{self.nickname} ({self.reward})"


class HuntLog(models.Model):
    # Один преступник: много попыток поимки (one-to-many)
    criminal = models.ForeignKey(
        WantedCriminal, on_delete=models.CASCADE, related_name="hunts"
    )
    success = models.BooleanField(default=False)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # ставится сервером автоматически

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Hunt #{self.pk} for criminal {self.criminal_id}"
