# Generated by Django 5.0 on 2024-01-16 02:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calapp', '0002_alter_appointment_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='owner',
            field=models.CharField(default='prdepinho', max_length=256),
            preserve_default=False,
        ),
    ]
