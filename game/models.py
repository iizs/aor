from django.db import models

import json

from player.models import Player
from rule.models import Edition

class GetOrNoneManager(models.Manager):
    """Adds get_or_none method to objects
    """
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

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
    hashkey = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    date_created = models.DateTimeField('datetime created', auto_now_add=True)
    date_started = models.DateTimeField('datetime started', null=True, blank=True)
    date_ended = models.DateTimeField('datetime ended', null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS, default=WAITING)
    players = models.ManyToManyField(Player, null=True, blank=True)
    initial_info = models.TextField(null=True, blank=True)
    current_info = models.TextField(null=True, blank=True)
    last_lsn = models.SmallIntegerField('last log sequence number', default=0)
    num_players = models.SmallIntegerField()
    edition = models.ForeignKey(Edition)

    objects = GetOrNoneManager()

    def __unicode__(self):
        return self.hashkey

    def to_dict(self):
        d = {}
        d['game_id'] = self.hashkey
        d['name'] = self.name
        d['date_created'] = str(self.date_created) if self.date_created != None else None 
        d['date_started'] = str(self.date_started) if self.date_started != None else None
        d['date_ended'] = str(self.date_ended) if self.date_ended != None else None
        d['status'] = self.status
        d['edition'] = str(self.edition)
        d['num_players'] = self.num_players
        d['players'] = []
        for p in self.players.all():
            d['players'].append(str(p))
        return d

    class UnableToDelete(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)
            
    class UnableToJoin(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)
            
    class UnableToQuit(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class UnableToStart(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

class GameLog(models.Model):
    ACCEPTED = 'A'
    CONFIRMED = 'C'
    FAILED = 'F'
    STATUS = (
        (ACCEPTED, 'Accepted'),
        (CONFIRMED, 'Confirmed'),
        (FAILED, 'Failed'),
    )
    game = models.ForeignKey('Game')
    player = models.ForeignKey(Player)
    lsn = models.SmallIntegerField('log sequence number')
    timestamp = models.DateTimeField('timestamp', auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS, default=ACCEPTED)
    log = models.TextField()

    class Meta:
        unique_together = (
            ("game", "lsn"),
        )

    class WriteFailed(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

class HouseBiddingLog:
    def __init__(self):
        self.user_id = None
        self.house = None
        self.bid = 0
        self.order = 0

# house name
class HouseTurnLog:
    def __init__(self):
        self.turn = 0
        self.cash = 0
        self.tokens = 0
        self.card_income = 0
        self.card_damage = 0
        self.buy_card = False
        self.ship_upgrade = False
        self.buy_advance = 0
        self.card_stabilization = 0
        self.tax = 0

    def written_cash(self):
        return self.cash - abs( self.token );

    #def current_cash(self):


class HouseStatus:
    def __init__(self):
        self.user_id = None
        self.misery = 0
        self.advances = {}
        self.hands = []
        self.cash = 40
        self.tokens = 0
        self.written_cash = 0
        self.ship_type = None
        self.ship_capacity = 0
        self.turn_logs = []
        self.turn_logs.append( HouseTurnLog() )

class GameStatus:
    HOUSES = ( 'Gen', 'Ven', 'Bar', 'Par', 'Lon', 'Ham' )

    def __init__(self, game=None):
        self.edition = None
        self.game_id = None
        self.num_players = 0

        self.houses = {}
        for h in self.HOUSES:
            self.houses[h] = HouseStatus()

        self.play_order = []
        self.house_bidding_log = []
        for n in range(6):
            self.play_order.append(None)

        self.epoch = 1
        self.state = None
        self.discard_stack = []
        self.draw_stack = []
        self.leader_stack = []
        self.shortage = []
        self.surplus = []
        self.provinces = {}
        self.card_log = {}
        self.card_log['epoch_1'] = {}
        self.card_log['epoch_2'] = {}
        self.card_log['epoch_3'] = {}
        self.at_war = []

        if game != None: 
            if isinstance(game, Game) != True:
                raise TypeError('game must be a Game instance')

            self.edition = str(game.edition)
            self.game_id = game.hashkey
            self.num_players = game.num_players

class GameStatusEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, GameStatus):
            return obj.__dict__
        if isinstance(obj, HouseStatus):
            return obj.__dict__
        if isinstance(obj, HouseTurnLog):
            return obj.__dict__
        if isinstance(obj, HouseBiddingLog):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

class GameStatusDecoder(json.JSONDecoder):
    def decode(self, s):
        d = json.JSONDecoder.decode(self, s)
        g = GameStatus()
        g.__dict__ = d

        house_bidding_log = []
        for l in g.house_bidding_log:
            hbl = HouseBiddingLog()
            hbl.__dict__ = l
            house_bidding_log.append(hbl)
        g.house_bidding_log = house_bidding_log

        houses = {}
        for key, value in g.houses.iteritems():
            h = HouseStatus()
            h.__dict__ = value
            turn_logs = []
            for l in h.turn_logs:
                tl = HouseTurnLog()
                tl.__dict__ = l
                turn_logs.append(tl)
            h.turn_logs = turn_logs

            houses[key] = h
        g.houses = houses

        return g
