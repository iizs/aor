# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name=b'datetime created')),
                ('date_started', models.DateTimeField(null=True, verbose_name=b'datetime started', blank=True)),
                ('date_ended', models.DateTimeField(null=True, verbose_name=b'datetime ended', blank=True)),
                ('status', models.CharField(default=b'W', max_length=1, choices=[(b'W', b'Waiting'), (b'P', b'In progress'), (b'E', b'Ended')])),
                ('initial_info', models.TextField(null=True, blank=True)),
                ('current_info', models.TextField(null=True, blank=True)),
                ('last_lsn', models.SmallIntegerField(verbose_name=b'last log sequence number')),
                ('players', models.ManyToManyField(to='player.Player', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GameLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lsn', models.SmallIntegerField(verbose_name=b'log sequence number')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name=b'timestamp')),
                ('log', models.TextField()),
                ('game', models.ForeignKey(to='game.Game')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='gamelog',
            unique_together=set([('game', 'lsn')]),
        ),
    ]
