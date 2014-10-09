from django.db import models
from player.models import Player

class Game(models.Model):
    WAITING = 'W'
    IN_PROGRESS = 'P'
    ENDED = 'E'
    STATUS = (
        (WAITING, 'Waiting'),
        (IN_PROGRESS, 'In progress'),
        (ENDED, 'Ended'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    date_created = models.DateTimeField('datetime created', auto_now_add=True)
    date_started = models.DateTimeField('datetime started', null=True, blank=True)
    date_ended = models.DateTimeField('datetime ended', null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS, default=WAITING)
    players = models.ManyToManyField(Player, null=True, blank=True)
    initial_info = models.TextField(null=True, blank=True)
    current_info = models.TextField(null=True, blank=True)
    last_lsn = models.SmallIntegerField('last log sequence number')

    def __unicode__(self):
        return self.id + ' ' + self.name

class GameLog(models.Model):
    game = models.ForeignKey('Game')
    lsn = models.SmallIntegerField('log sequence number')
    timestamp = models.DateTimeField('timestamp', auto_now_add=True)
    log = models.TextField()

    class Meta:
        unique_together = (
            ("game", "lsn"),
        )
