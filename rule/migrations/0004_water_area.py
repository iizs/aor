# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0003_auto_20141001_0710'),
    ]

    operations = [
        migrations.AddField(
            model_name='water',
            name='area',
            field=models.CharField(default='X', max_length=1, choices=[(b'1', b'I'), (b'2', b'II'), (b'3', b'III'), (b'4', b'IV'), (b'5', b'V'), (b'6', b'VI'), (b'7', b'VII'), (b'8', b'VIII'), (b'F', b'Far East'), (b'N', b'New World'), (b'X', b'Not Defined')]),
            preserve_default=False,
        ),
    ]
