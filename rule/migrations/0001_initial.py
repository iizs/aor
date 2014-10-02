# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Commodity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=2)),
                ('full_name', models.CharField(max_length=10)),
                ('unit_price', models.SmallIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Edition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('area', models.CharField(max_length=1, choices=[(b'1', b'I'), (b'2', b'II'), (b'3', b'III'), (b'4', b'IV'), (b'5', b'V'), (b'6', b'VI'), (b'7', b'VII'), (b'8', b'VIII'), (b'F', b'Far East'), (b'N', b'New World'), (b'X', b'Not Defined')])),
                ('full_name', models.CharField(max_length=20)),
                ('short_name', models.CharField(max_length=10)),
                ('province_type', models.CharField(max_length=1, verbose_name=b'Type', choices=[(b'C', b'Capital'), (b'P', b'Province'), (b'S', b'Satellite')])),
                ('market_size', models.SmallIntegerField()),
                ('commodities', models.ManyToManyField(to='rule.Commodity', null=True)),
                ('connected', models.ManyToManyField(related_name='connected_rel_+', null=True, to='rule.Province')),
                ('edition', models.ForeignKey(to='rule.Edition')),
                ('supports', models.ManyToManyField(related_name='supports_rel_+', null=True, to='rule.Province')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Water',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(max_length=20)),
                ('short_name', models.CharField(max_length=10)),
                ('water_type', models.CharField(max_length=1, choices=[(b'C', b'Coast'), (b'S', b'Sea')])),
                ('coast_of', models.ForeignKey(to='rule.Province', null=True)),
                ('connected', models.ManyToManyField(related_name='connected_rel_+', null=True, to='rule.Water')),
                ('edition', models.ForeignKey(to='rule.Edition')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
