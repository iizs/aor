# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0010_auto_20141007_0948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historycard',
            name='recycles',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='historycard',
            name='shuffle_later',
            field=models.BooleanField(default=False),
        ),
    ]
