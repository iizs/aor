# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0008_auto_20141004_1533'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='province',
            name='x',
        ),
        migrations.RemoveField(
            model_name='province',
            name='y',
        ),
    ]
