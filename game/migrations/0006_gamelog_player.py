# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0002_auto_20141013_1433'),
        ('game', '0005_gamelog_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamelog',
            name='player',
            field=models.ForeignKey(default=1, to='player.Player'),
            preserve_default=False,
        ),
    ]
