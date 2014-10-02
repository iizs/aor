# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='province',
            unique_together=set([('edition', 'full_name'), ('edition', 'short_name')]),
        ),
    ]
