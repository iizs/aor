# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_gamelog_player'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gamelog',
            name='player',
            field=models.ForeignKey(blank=True, to='player.Player', null=True),
        ),
    ]
