from datetime import timedelta
from decimal import Decimal

from django.db import migrations
from django.utils import timezone

# 6 преступников: разные награды и признаки, чтобы фильтры и сортировка давали разные результаты
CRIMINALS = [
    dict(name="Vex Kallister", nickname="Black Comet", reward=Decimal("25000.00"),
         latitude=15.5, longitude=-42.3, location_note="Last seen near the Titan docking ring",
         difficulty=8, armed=True, has_crew=True, escape_master=True),
    dict(name=None, nickname="The Ghost", reward=Decimal("50000.00"),
         latitude=None, longitude=None, location_note="Rumored to hide in the Kuiper belt",
         difficulty=10, armed=False, has_crew=False, escape_master=True),
    dict(name="Mara Voss", nickname="Red Siren", reward=Decimal("7500.00"),
         latitude=-33.9, longitude=151.2, location_note="",
         difficulty=5, armed=True, has_crew=False, escape_master=False),
    dict(name="Dorn Haskel", nickname="Iron Jaw", reward=Decimal("3200.00"),
         latitude=None, longitude=None, location_note="Mining station Ceres-9",
         difficulty=3, armed=True, has_crew=True, escape_master=False),
    dict(name="Lio Tarn", nickname="Slippery Lio", reward=Decimal("12000.00"),
         latitude=51.5, longitude=-0.12, location_note="Smuggling lane near Mars orbit",
         difficulty=6, armed=False, has_crew=True, escape_master=True),
    dict(name=None, nickname="Pixel", reward=Decimal("1800.00"),
         latitude=None, longitude=None, location_note="Hacker, location unknown",
         difficulty=2, armed=False, has_crew=False, escape_master=False),
]

# 12 записей журнала: (номер преступника по порядку, success, notes)
HUNTS = [
    (1, False, "Target escaped through an asteroid field."),
    (1, False, "Crew ambushed us at the Titan docking ring."),
    (1, False, "Lost the trail after a hyperspace jump."),
    (2, False, "Only found an empty ship drifting in the Kuiper belt."),
    (2, False, "Informant sold us a false location."),
    (3, True, "Captured at a fuel station on Europa without a shot fired."),
    (3, False, "She slipped away in the crowd at the Luna market."),
    (4, True, "Arrested at Ceres-9 after a short chase."),
    (4, True, "Caught again, he never learns."),
    (5, False, "Escaped through a smuggler tunnel under the station."),
    (5, False, "His crew blocked the docking bay."),
    (5, True, "Finally cornered near Mars orbit, delivered to the authorities."),
]


def seed(apps, schema_editor):
    WantedCriminal = apps.get_model("bounty", "WantedCriminal")
    HuntLog = apps.get_model("bounty", "HuntLog")

    created = [WantedCriminal.objects.create(**data) for data in CRIMINALS]

    now = timezone.now()
    for index, (num, success, notes) in enumerate(HUNTS):
        log = HuntLog.objects.create(criminal=created[num - 1], success=success, notes=notes)
        # created_at ставится автоматически; разносим записи по времени для реалистичности
        HuntLog.objects.filter(pk=log.pk).update(created_at=now - timedelta(days=len(HUNTS) - index))


def unseed(apps, schema_editor):
    apps.get_model("bounty", "HuntLog").objects.all().delete()
    apps.get_model("bounty", "WantedCriminal").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("bounty", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
