# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0011_auto_20141007_0949'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='commoditycard',
            unique_together=None,
        ),
        migrations.AlterUniqueTogether(
            name='eventcard',
            unique_together=None,
        ),
        migrations.AlterUniqueTogether(
            name='leadercard',
            unique_together=None,
        ),
    ]
