# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0007_auto_20141002_0313'),
    ]

    operations = [
        migrations.AddField(
            model_name='province',
            name='x',
            field=models.SmallIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='province',
            name='y',
            field=models.SmallIntegerField(default=0),
            preserve_default=True,
        ),
    ]
