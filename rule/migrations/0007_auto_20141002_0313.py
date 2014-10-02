# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0006_auto_20141002_0241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='water',
            name='full_name',
            field=models.CharField(max_length=30),
        ),
    ]
