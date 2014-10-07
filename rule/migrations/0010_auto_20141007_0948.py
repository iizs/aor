# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rule', '0009_auto_20141007_0604'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=1)),
                ('full_name', models.CharField(max_length=40)),
                ('category', models.CharField(max_length=1, choices=[(b'S', b'Science'), (b'R', b'Religion'), (b'C', b'Commerce'), (b'M', b'Communication'), (b'E', b'Exploration'), (b'V', b'Civics')])),
                ('points', models.SmallIntegerField()),
                ('credits', models.SmallIntegerField()),
                ('edition', models.ForeignKey(to='rule.Edition')),
                ('prerequisites', models.ManyToManyField(related_name='prerequisites_rel_+', null=True, to='rule.Advance', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoryCard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(max_length=40)),
                ('short_name', models.CharField(max_length=10)),
                ('epoch', models.SmallIntegerField()),
                ('recycles', models.BooleanField()),
                ('shuffle_later', models.BooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventCard',
            fields=[
                ('historycard_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='rule.HistoryCard')),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=('rule.historycard',),
        ),
        migrations.CreateModel(
            name='CommodityCard',
            fields=[
                ('historycard_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='rule.HistoryCard')),
                ('commodities', models.ManyToManyField(to='rule.Commodity')),
            ],
            options={
            },
            bases=('rule.historycard',),
        ),
        migrations.CreateModel(
            name='LeaderCard',
            fields=[
                ('historycard_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='rule.HistoryCard')),
                ('discount', models.SmallIntegerField()),
                ('discount_on_event', models.SmallIntegerField(null=True, blank=True)),
                ('discount_after_event', models.BooleanField(default=False)),
                ('discount_during_event', models.BooleanField(default=False)),
                ('advances', models.ManyToManyField(to='rule.Advance')),
                ('event', models.ForeignKey(blank=True, to='rule.EventCard', null=True)),
            ],
            options={
            },
            bases=('rule.historycard',),
        ),
        migrations.AddField(
            model_name='historycard',
            name='edition',
            field=models.ForeignKey(to='rule.Edition'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='historycard',
            unique_together=set([('edition', 'short_name')]),
        ),
    ]
