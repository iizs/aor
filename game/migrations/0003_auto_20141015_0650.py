# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0014_advance_prerequisites'),
        ('game', '0002_game_hashkey'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='edition',
            field=models.ForeignKey(default=1, to='rule.Edition'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='num_players',
            field=models.SmallIntegerField(default=6),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='game',
            name='last_lsn',
            field=models.SmallIntegerField(default=0, verbose_name=b'last log sequence number'),
        ),
    ]
