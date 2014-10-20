# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0007_auto_20141018_1334'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='applied_lsn',
            field=models.SmallIntegerField(default=0, verbose_name=b'last log sequence number applied'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='game',
            name='last_lsn',
            field=models.SmallIntegerField(default=0, verbose_name=b'last log sequence number submitted'),
        ),
    ]
