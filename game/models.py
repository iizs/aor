# -*- coding: utf-8 -*-
from django.db import models

from celery.utils.log import get_task_logger

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
        self.dice_rolled = []

# house name
class HouseTurnLog(object):
    def __init__(self, turn=0, cash=0):
        self.turn = turn
        self.cash = cash
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
    SHIP_GALLEY = 'galley'
    SHIP_SEAWROTHY = 'seaworthy'
    SHIP_OCEANGOING = 'oceangoing'

    def __init__(self, user_id=None, cash=40, hands=[]):
        self.user_id = user_id
        self.misery = 0
        self.advances = {}
        self.hands = hands
        self.cash = cash
        self.tokens = 0
        self.written_cash = 0
        self.ship_type = HouseInfo.SHIP_GALLEY
        self.ship_capacity = 0
        self.turn_logs = []

class GameInfo(object):
    GEN = 'Gen'
    VEN = 'Ven'
    BAR = 'Bar'
    PAR = 'Par'
    LON = 'Lon'
    HAM = 'Ham'
    HOUSES = ( GEN, VEN, BAR, PAR, LON, HAM )

    SHUFFLE_INIT = 0
    SHUFFLE_TURN1 = 1
    SHUFFLE_TURN2 = 2

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
        self.turn = 1
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

    def shuffle_cards(self, method, rand_dict):
        cards = []
        edition = Edition.objects.filter(name__exact=self.edition)

        if 'draw_stack' in rand_dict.keys():
            cards = rand_dict['draw_stack']
        else :
            if method == GameInfo.SHUFFLE_INIT :
                hcards = HistoryCard.objects                    \
                            .filter(edition__exact=edition)     \
                            .filter(epoch__exact=1)             \
                            .filter(shuffle_later__exact=False)
                for c in hcards:
                    cards.append(c.short_name)
            elif method == GameInfo.SHUFFLE_TURN1 :
                cards = self.discard_stack + self.draw_stack
                if self.num_players in (3, 4) :
                    hcards = HistoryCard.objects                    \
                                .filter(edition__exact=edition)     \
                                .filter(epoch__exact=1)             \
                                .filter(shuffle_later__exact=True)
                    for c in hcards:
                        cards.append(c.short_name)
            elif method == GameInfo.SHUFFLE_TURN2 :
                if self.num_players in (5, 6) :
                    hcards = HistoryCard.objects                    \
                                .filter(edition__exact=edition)     \
                                .filter(epoch__exact=1)             \
                                .filter(shuffle_later__exact=True)
                    for c in hcards:
                        cards.append(c.short_name)
            else:
                pass
            random.shuffle(cards)

        self.draw_stack = cards
        if method == GameInfo.SHUFFLE_TURN2 :
            return
        self.discard_stack = []

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
    DEAL_CARDS      =   'deal_cards'
    DISCARD         =   'discard'
    BID             =   'bid'
    CHOOSE          =   'choose'
    DETERMINE_ORDER =   'determine_order'

    class InvalidParameter(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

class GameState(object):
    ALL             =   'all'
    AUTO            =   'auto'

    INITIALIZE      =   'init'
    HOUSE_BIDDING   =   'housebidding'
    CHOOSE_CAPITAL  =   'choose_capital'
    TOKEN_BIDDING  =   'token_bidding'

    STATE_MAPS = {
        INITIALIZE : 'InitState',
        HOUSE_BIDDING : 'HouseBiddingState',
        CHOOSE_CAPITAL  :   'ChooseCapitalState',
        TOKEN_BIDDING  :   'TokenBiddingState',
    }

    def __init__(self, info, actor='all', depends_on=None):
        self.info = info
        self.actor = actor
        self.depends_on = depends_on

    def action(self, a, user_id=None, params={}):
        raise GameState.NotSupportedAction(type(self).__name__ + ' cannot handle ' + a) 

    @staticmethod
    def getInstance(info):
        state_part = info.state.split('.', 3)
        name = state_part[1]
        actor = state_part[0]
        remains = state_part[2] if len(state_part) == 3 else None
        n = GameState.STATE_MAPS[name] if name in GameState.STATE_MAPS.keys() else None
        return globals()[n](info, actor=actor, depends_on=remains) if n in globals().keys() else None

    class NotSupportedAction(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class InvalidAction(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

class InitState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.DEAL_CARDS :
            # 초기화 상태이니, 무조건 카드를 섞고, 배분한다.
            # log replay를 하는 경우에는 과거에 섞은것과 동일하게 섞는다.
            rand_dict = params['random'] if 'random' in params.keys() else {}
            self.info.shuffle_cards(GameInfo.SHUFFLE_INIT, rand_dict)

            rand_dict['draw_stack'] = list(self.info.draw_stack)
            for h in self.info.house_bidding_log:
                h.draw_cards.append(self.info.draw_stack.pop())
                h.draw_cards.append(self.info.draw_stack.pop())
                h.draw_cards.append(self.info.draw_stack.pop())
            self.info.state = GameState.ALL + '.' + GameState.HOUSE_BIDDING
            return { 'random': rand_dict }
        else:
            return super(InitState, self).action(a, params)

def cmp_house_bid(x, y):
    diff = x.bid - y.bid
    i = 0
    while diff == 0 and i < len(x.dice_rolled) and i < len(y.dice_rolled) : 
        diff = x.dice_rolled[i] - y.dice_rolled[i]
        i += 1
    return diff

def roll_dice():
    return random.randint(1, 6)

def roll_dices():
    return { 
        "white": roll_dice(),
        "black": roll_dice(),
        "green": roll_dice(),
    }
    
class HouseBiddingState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.DISCARD :
            if user_id == None :
                raise Action.InvalidParameter(Action.DISCARD + " requires 'used_id'")
            if 'card' not in params.keys() :
                raise Action.InvalidParameter(Action.DISCARD + " requires 'card' parameter.")
            for h in self.info.house_bidding_log:
                if h.user_id == user_id :
                    if h.discard_card != None:
                        raise GameState.InvalidAction( 
                                "User '" + user_id + "' already discarded '" + h.discard_card + "'"
                                )
                    if params['card'] not in h.draw_cards:
                        raise Action.InvalidParameter( 
                                "User '" + user_id + "' cannot discard '" + params['card'] + "'"
                                )
                    h.draw_cards.remove(params['card'])
                    h.discard_card = params['card']
                    self.info.discard_stack.append(params['card'])
        elif a == Action.BID :
            if user_id == None :
                raise Action.InvalidParameter(Action.BID + " requires 'used_id'")
            if 'bid' not in params.keys() :
                raise Action.InvalidParameter(Action.BID + " requires 'bid' parameter.")
            for h in self.info.house_bidding_log:
                if h.user_id == user_id :
                    h.bid = int(params['bid'])
        elif a == Action.DETERMINE_ORDER :
            tie_breaking = True

            if 'random' in params.keys() :
                rand_dict = params['random']
                for l in self.info.house_bidding_log:
                    l.dice_rolled = rand_dict[l.user_id]
                    tie_breaking = False

            self.info.house_bidding_log.sort(cmp=cmp_house_bid, reverse=True)

            while tie_breaking :
                roll = {}
                for i in range(len(self.info.house_bidding_log)-1):
                    for j in range(i+1, len(self.info.house_bidding_log)):
                        if cmp_house_bid(self.info.house_bidding_log[i], self.info.house_bidding_log[j]) == 0 :
                            roll[i] = True
                            roll[j] = True
                if roll:
                    for i in roll.keys():
                        self.info.house_bidding_log[i].dice_rolled.append(roll_dice())
                    self.info.house_bidding_log.sort(cmp=cmp_house_bid, reverse=True)
                else:
                    tie_breaking = False

            self.info.state = self.info.house_bidding_log[0].user_id + '.' + GameState.CHOOSE_CAPITAL

            rand_dict = {}
            for l in self.info.house_bidding_log:
                rand_dict[l.user_id] = l.dice_rolled
            return { 'random': rand_dict  }
        else:
            return super(HouseBiddingState, self).action(a, params)

        bidding_complete = True
        for h in self.info.house_bidding_log:
            if h.discard_card != None and h.bid != None:
                continue
            bidding_complete = False
            break

        if bidding_complete == True:
            return { 'queue_action': { 'action': Action.DETERMINE_ORDER } }
        return {}

class ChooseCapitalState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.CHOOSE :
            if user_id != self.actor :
                raise GameState.InvalidAction( 
                        "Not user '" + user_id + "' turn"
                        )
            if 'choice' not in params.keys() :
                raise Action.InvalidParameter(Action.CHOOSE + " requires 'choice' parameter.")
            choice = params['choice']

            available = list(GameInfo.HOUSES[0:self.info.num_players])
            for h in self.info.houses.keys():
                available.remove(h)

            if choice not in available:
                raise Action.InvalidParameter("'" + choice + "' is already chosen or not allowed.")

            bidinfo = self.info.house_bidding_log[len(self.info.houses)]

            h = HouseInfo(
                    user_id=user_id,
                    hands = list(bidinfo.draw_cards),
                    cash = 40 - bidinfo.bid,
            )
            self.info.houses[choice] = h

            if len(self.info.houses) < self.info.num_players:
                self.info.state = self.info.house_bidding_log[len(self.info.houses)].user_id \
                                    + '.' + GameState.CHOOSE_CAPITAL
            else:
                self.info.state = GameState.ALL + '.' + GameState.TOKEN_BIDDING
                self.info.epoch = 1
                self.info.turn = 1
                for key in self.info.houses:
                    h = self.info.houses[key]
                    h.turn_logs.append( 
                        HouseTurnLog(
                            turn=self.info.turn,
                            cash=h.cash,
                            ) 
                        )

            return {}
        else:
            return super(ChooseCapitalState, self).action(a, params)

class TokenBiddingState(GameState):
    def action(self, a, user_id=None, params={}):
        return super(TokenBiddingState, self).action(a, params)
