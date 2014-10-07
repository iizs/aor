# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0013_remove_advance_prerequisites'),
    ]

    operations = [
        migrations.AddField(
            model_name='advance',
            name='prerequisites',
            field=models.ManyToManyField(to='rule.Advance', null=True, blank=True),
            preserve_default=True,
        ),
    ]
