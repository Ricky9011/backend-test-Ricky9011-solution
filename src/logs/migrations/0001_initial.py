# Generated by Django 5.1.2 on 2024-11-20 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OutboxLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_type",
                    models.CharField(max_length=255, verbose_name="Event Type"),
                ),
                (
                    "event_date_time",
                    models.DateTimeField(verbose_name="Event Date Time"),
                ),
                (
                    "environment",
                    models.CharField(max_length=7, verbose_name="Environment"),
                ),
                ("event_context", models.TextField(verbose_name="Event Context")),
                (
                    "metadata_version",
                    models.BigIntegerField(verbose_name="Metadata Version"),
                ),
                (
                    "exported_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Exported At",
                    ),
                ),
            ],
            options={
                "verbose_name": "Outbox Log",
                "verbose_name_plural": "Outbox Logs",
            },
        ),
    ]
