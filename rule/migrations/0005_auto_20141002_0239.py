# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0004_water_area'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='water',
            unique_together=set([('edition', 'full_name'), ('edition', 'short_name')]),
        ),
    ]
