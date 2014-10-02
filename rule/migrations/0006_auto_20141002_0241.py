# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0005_auto_20141002_0239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='water',
            name='coast_of',
            field=models.ForeignKey(blank=True, to='rule.Province', null=True),
        ),
        migrations.AlterField(
            model_name='water',
            name='connected',
            field=models.ManyToManyField(related_name='connected_rel_+', null=True, to=b'rule.Water', blank=True),
        ),
    ]
