# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_auto_20141015_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamelog',
            name='status',
            field=models.CharField(default=b'A', max_length=1, choices=[(b'A', b'Accepted'), (b'C', b'Confirmed'), (b'F', b'Failed')]),
            preserve_default=True,
        ),
    ]
