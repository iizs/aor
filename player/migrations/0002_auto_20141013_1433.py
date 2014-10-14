# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(max_length=255, db_index=True)),
                ('expires', models.DateTimeField()),
                ('player', models.OneToOneField(to='player.Player')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='player',
            name='auth_provider',
            field=models.CharField(default=b'i', max_length=1, choices=[(b'i', b'iizs.net'), (b'g', b'Google ID'), (b'k', b'KAKAO ID')]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='player',
            unique_together=set([('auth_provider', 'user_id')]),
        ),
    ]
