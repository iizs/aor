# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_auto_20141020_0911'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamelog',
            name='msg',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
