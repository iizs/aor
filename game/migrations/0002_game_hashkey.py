# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='hashkey',
            field=models.CharField(default='', unique=True, max_length=255, db_index=True),
            preserve_default=False,
        ),
    ]
