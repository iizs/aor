# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0002_auto_20141001_0555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='province',
            name='commodities',
            field=models.ManyToManyField(to=b'rule.Commodity', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='province',
            name='connected',
            field=models.ManyToManyField(related_name='connected_rel_+', null=True, to=b'rule.Province', blank=True),
        ),
        migrations.AlterField(
            model_name='province',
            name='supports',
            field=models.ManyToManyField(related_name='supports_rel_+', null=True, to=b'rule.Province', blank=True),
        ),
    ]
