# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0012_auto_20141007_0950'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='advance',
            name='prerequisites',
        ),
    ]
