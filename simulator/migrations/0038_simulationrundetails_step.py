# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-23 14:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0037_simulationrundetails_line'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulationrundetails',
            name='step',
            field=models.FloatField(default=0),
        ),
    ]
