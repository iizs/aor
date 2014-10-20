# -*- coding: utf-8 -*-
from django.db import models

import json
import random

from player.models import Player
from rule.models import Edition, HistoryCard, EventCard, LeaderCard, CommodityCard

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
    last_lsn = models.SmallIntegerField('last log sequence number submitted', default=0)
    applied_lsn = models.SmallIntegerField('last log sequence number applied', default=0)
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
        d['last_lsn'] = self.last_lsn
        d['applied_lsn'] = self.applied_lsn
        d['players'] = []
        for p in self.players.all():
            d['players'].append(str(p))
        return d

    def set_current_info(self, info):
        self.current_info = json.dumps(info, cls=GameInfoEncoder)

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
    player = models.ForeignKey(Player, null=True, blank=True)
    lsn = models.SmallIntegerField('log sequence number')
    timestamp = models.DateTimeField('timestamp', auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS, default=ACCEPTED)
    log = models.TextField()

    def __unicode__(self):
        return str(self.game) + ': ' + str(self.lsn)
    def set_log(self, log_dict={}):
        ''' convert log dict info json and store to log field '''
        log_json = json.dumps(log_dict)
        self.log = log_json

    def get_log_as_dict(self):
        return json.loads(self.log)

    class Meta:
        unique_together = (
            ("game", "lsn"),
        )

    class WriteFailed(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

class HouseBiddingLog(object):
    def __init__(self):
        self.user_id = None
        self.house = None
        self.bid = None
        self.order = None
        self.draw_cards = []
        self.discard_card = None

# house name
class HouseTurnLog(object):
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


class HouseInfo(object):
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

class GameInfo(object):
    GEN = 'Gen'
    VEN = 'Ven'
    BAR = 'Bar'
    PAR = 'Par'
    LON = 'Lon'
    HAM = 'Ham'
    HOUSES = ( GEN, VEN, BAR, PAR, LON, HAM )

    def __init__(self, game=None):
        self.edition = 'european' #None
        self.game_id = None
        self.num_players = 0

        self.houses = {}
        #for h in self.HOUSES:
            #self.houses[h] = HouseInfo()

        self.play_order = []
        self.house_bidding_log = []
        for n in range(6):
            self.play_order.append(None)

        self.epoch = 1
        self.state = GameState.AUTO + '.' + GameState.INITIALIZE
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
            for p in game.players.all():
                h = HouseBiddingLog()
                h.user_id = p.user_id
                self.house_bidding_log.append(h)

    def shuffle_cards(self, epoch):
        cards = []
        edition = Edition.objects.filter(name__exact=self.edition)
        if epoch == 0 :
            hcards = HistoryCard.objects                    \
                        .filter(edition__exact=edition)     \
                        .filter(epoch__exact=1)             \
                        .filter(shuffle_later__exact=False)
            for c in hcards:
                cards.append(c.short_name)
        else:
            pass

        random.shuffle(cards)
        self.discard_stack = []
        self.draw_stack = cards

    def draw_initial_cards(self):
        for h in self.house_bidding_log:
            h.draw_cards.append(self.draw_stack.pop())
            h.draw_cards.append(self.draw_stack.pop())
            h.draw_cards.append(self.draw_stack.pop())

class GameInfoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, GameInfo):
            return obj.__dict__
        if isinstance(obj, HouseInfo):
            return obj.__dict__
        if isinstance(obj, HouseTurnLog):
            return obj.__dict__
        if isinstance(obj, HouseBiddingLog):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

class GameInfoDecoder(json.JSONDecoder):
    def decode(self, s):
        d = json.JSONDecoder.decode(self, s)
        g = GameInfo()
        g.__dict__ = d

        house_bidding_log = []
        for l in g.house_bidding_log:
            hbl = HouseBiddingLog()
            hbl.__dict__ = l
            house_bidding_log.append(hbl)
        g.house_bidding_log = house_bidding_log

        houses = {}
        for key, value in g.houses.iteritems():
            h = HouseInfo()
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

class Action(object):
    DEAL_CARDS =   'deal_cards'

class GameState(object):
    ALL             =   'all'
    AUTO            =   'auto'

    INITIALIZE      =   'init'
    HOUSE_BIDDING   =   'housebidding'

    STATE_MAPS = {
        INITIALIZE : 'InitState',
        HOUSE_BIDDING : 'HouseBiddingState',
    }

    def __init__(self, info):
        self.info = info

    def action(self, a, params={}):
        raise GameState.NotSupportedAction(type(self).__name__ + ' cannot handle ' + type(a).__name__) 

    @staticmethod
    def getInstance(info):
        state_part = info.state.split('.', 3)
        name = state_part[1]
        n = GameState.STATE_MAPS[name] if name in GameState.STATE_MAPS.keys() else None
        return globals()[n](info) if n in globals().keys() else None

    class NotSupportedAction(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

class InitState(GameState):
    def action(self, a, params={}):
        if a == Action.DEAL_CARDS :
            # 초기화 상태이니, 무조건 카드를 섞고, 배분한다.
            self.info.shuffle_cards(0)
            self.info.draw_initial_cards()
            self.info.state = GameState.ALL + '.' + GameState.HOUSE_BIDDING
        else:
            return super(InitState, self).action(a, params)

class HouseBiddingState(GameState):
    def action(self, a, params={}):
        return super(HouseBiddingState, self).action(a, params)
