# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0014_advance_prerequisites'),
    ]

    operations = [
        migrations.AddField(
            model_name='commodity',
            name='dice_roll',
            field=models.SmallIntegerField(default=2),
            preserve_default=False,
        ),
    ]
