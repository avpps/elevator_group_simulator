# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-23 14:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0036_auto_20170620_0850'),
    ]

    operations = [
        migrations.AddField(
            model_name='simulationrundetails',
            name='line',
            field=models.TextField(default=0),
        ),
    ]
