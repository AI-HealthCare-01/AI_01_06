from tortoise import fields
from tortoise.models import Model


class MedicationSchedule(Model):
    id = fields.IntField(primary_key=True)
    medication = fields.ForeignKeyField("models.Medication", related_name="schedules")
    time_of_day = fields.CharField(max_length=20)  # MORNING|NOON|EVENING|BEDTIME
    specific_time = fields.TimeField(null=True)
    start_date = fields.DateField(null=True)
    end_date = fields.DateField(null=True)

    class Meta:
        table = "medication_schedules"


class AdherenceLog(Model):
    id = fields.IntField(primary_key=True)
    schedule = fields.ForeignKeyField("models.MedicationSchedule", related_name="logs")
    actor_user = fields.ForeignKeyField("models.User", related_name="adherence_logs")
    target_date = fields.DateField()
    status = fields.CharField(max_length=20)  # TAKEN|MISSED|SKIPPED
    logged_at = fields.DatetimeField(auto_now_add=True)
    note = fields.TextField(null=True)

    class Meta:
        table = "adherence_logs"
