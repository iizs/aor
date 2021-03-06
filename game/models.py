# -*- coding: utf-8 -*-
from django.db import models

from celery.utils.log import get_task_logger

import json
import random

from player.models import Player
from rule.models import Edition, HistoryCard, EventCard, LeaderCard, CommodityCard, Province, Commodity, Water
from rule.models import AREA_FAR_EAST, AREA_NEW_WORLD, AREA_VI, AREA_I, AREA_II, AREA_III

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
    msg = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return str(self.game) + ': ' + str(self.lsn)
    def set_log(self, log_dict={}):
        ''' convert log dict info json and store to log field '''
        log_json = json.dumps(log_dict)
        self.log = log_json

    def get_log_as_dict(self):
        return json.loads(self.log)

    def add_warning(self, user_id, msg):
        self._add_msg( user_id, msg={ 'type':'warning', 'msg':msg } )

    def add_info(self, user_id, msg):
        self._add_msg( user_id, msg={ 'type':'info', 'msg':msg } )

    def _add_msg(self, user_id, msg):
        if user_id == None or user_id == 'all' or user_id == 'auto' :
            # send to all
            user_list = []
            for p in self.game.players:
                user_list.append(p.user_id)
        else :
            user_list = [ user_id ]

        if self.msg == None:
            m = {}
        else :
            m = json.loads(self.msg)
        
        for u in user_list:
            if u not in m.keys():
                m[u] = []

            m[u].append( msg )

        self.msg = json.dumps(m)

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

    def mask(self, user_id, bid_in_progress):
        if self.user_id != user_id:
            self.draw_cards = []
            self.discard_card = None
            if bid_in_progress == True:
                self.bid = None

# house name
class HouseTurnLog(object):
    def __init__(self, turn=0, cash=0):
        self.turn = turn
        self.cash = cash
        self.tokens = None
        self.card_income = 0
        self.card_damage = 0
        self.buy_card = False
        self.ship_upgrade = False
        self.buy_advance = 0
        self.card_stabilization = 0
        self.tax = 0
        self.play_order = None

    def written_cash(self):
        return self.cash - abs( self.token );

    #def current_cash(self):
    def mask(self, bid_in_progress):
        if bid_in_progress == True:
            self.tokens = None
        self.card_income = 0
        self.card_damage = 0
        self.buy_card = False
        self.ship_upgrade = False
        self.buy_advance = 0
        self.card_stabilization = 0
        self.tax = 0

class HouseInfo(object):
    SHIP_GALLEY = 'galley'
    SHIP_SEAWROTHY = 'seaworthy'
    SHIP_OCEANGOING = 'oceangoing'

    def __init__(self, house_name=None, user_id=None, cash=40, hands=[]):
        self.user_id = user_id
        self.house_name = house_name
        self.misery = 0
        self.advances = {}
        self.hands = hands
        self.cash = cash
        self.dominance_marker = 25
        self.stock_tokens = 36
        self.expansion_tokens = 0
        self.ship_type = None
        self.ship_capacity = 0
        self.turn_logs = []
        self.chaos_out = False

    def mask(self, user_id, turn, bid_in_progress):
        if self.user_id != user_id:
            self.hands = None
            self.cash = None

            for l in self.turn_logs :
                if l.turn != turn:
                    l.mask(False)
                else :
                    l.mask(bid_in_progress)

    def prepare_new_turn(self, turn):
        self.stock_tokens += self.expansion_tokens
        self.expansion_tokens = 0
        self.turn_logs.append( 
            HouseTurnLog(
                turn=turn,
                cash=self.cash,
            ) 
        )

    def adjust_misery(self, level):
        if level != 0 :
            c_level = GameInfo.MISERY.index(self.misery)
            n_level = c_level + level

            if n_level < 0 : 
                n_level = 0
            if n_level >= len(GameInfo.MISERY): 
                n_level = len(GameInfo.MISERY) - 1
                self.chaos_out = True

            self.misery = GameInfo.MISERY[n_level]

class GameInfo(object):
    GEN = 'Gen'
    VEN = 'Ven'
    BAR = 'Bar'
    PAR = 'Par'
    LON = 'Lon'
    HAM = 'Ham'
    HOUSES = ( GEN, VEN, BAR, PAR, LON, HAM )

    MISERY = [  0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
                125, 150, 175, 200, 
                250, 300, 350, 400, 450, 500, 
                600, 700, 800, 900, 1000, "Chaos" ]

    SHUFFLE_INIT = 0
    SHUFFLE_TURN1 = 1
    SHUFFLE_TURN2 = 2
    SHUFFLE_NEXT_EPOCH = 3

    def __init__(self, game=None):
        self.edition = 'european' #None
        self.game_id = None
        self.num_players = 0

        self.houses = {}

        self.play_order = []
        self.play_order_tie_break = {}
        self.house_bidding_log = []

        self.epoch = 1
        self.turn = 1
        self.final_turn = False
        self.state = GameState.AUTO + '.' + GameState.INITIALIZE
        self.discard_stack = []
        self.draw_stack = []
        self.shortage = []
        self.surplus = []
        self.provinces = {}
        self.card_log = {}
        self.card_log['epoch_1'] = {}
        self.card_log['epoch_2'] = {}
        self.card_log['epoch_3'] = {}
        self.reset_war_info()
        self.leader = {
            'stack' : [],
            'player' : {},
            'user': {},
            'play_log': {},
        }
        self.renaissance_usage = {}
        self.enlightened_ruler = None
        self.civil_war = None
        self.papal_decree = []
        self.armor = None
        self.stirrups = None
        self.longbow = None
        self.gunpowder = None
        self.crusades = None
        self.mongol_armies = False
        self.religious_strife = False
        self.marker_removal = {}

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

    def mask(self, user_id):
        self.draw_stack = []
        bid_in_progress = self.state == GameState.ALL + '.' + GameState.TOKEN_BIDDING
        for key in self.houses:
            self.houses[key].mask(user_id, self.turn, bid_in_progress)

        bid_in_progress = self.state == GameState.ALL + '.' + GameState.HOUSE_BIDDING
        for l in self.house_bidding_log:
            l.mask(user_id, bid_in_progress)

    def getHouseInfo(self, key):
        try:
            return self.houses[key]
        except KeyError as e:
            raise GameInfo.HouseNotFound("'" + key  + "' is not a valid player name.")

    def getTurnLog(self, key, turn=None):
        ''' turn is 1-based '''
        if turn == None:
            turn = self.turn
        return self.getHouseInfo(key).turn_logs[turn - 1]

    def prepare_new_turn(self):
        self.clear_play_order()

        self.leader['stack'] = []
        self.leader['player'] = {}
        self.leader['user'] = {}

        self.renaissance_usage = {}
        self.enlightened_ruler = None
        self.civil_war = None
        self.papal_decree = []

        self.armor = None
        self.stirrups = None
        self.longbow = None
        self.gunpowder = None

        self.crusades = None
        if self.epoch != 3 :
            self.religious_strife = False

    def reset_war_info(self):
        self.war = {
            'attacker' : None,
            'defender' : None,
            'last_rolled_state' : None,
            'winner': None,
            'loser': None,
            'difference': None,
            'available_provinces': None,
        }

    def get_house_choice_order(self, player) :
        for i in range(len(self.house_bidding_log)):
            if self.house_bidding_log[i].user_id == player :
                return i
        # Exception을 raise하는 것이 더 좋을지도...
        return None

    def is_valid_player(self, player):
        return player in self.info.houses.keys()

    def clear_play_order(self):
        self.play_order = []

    def append_play_order(self, player):
        if ( self.num_players == 3 and len(self.play_order) in (0, 2, 4) ) \
            or ( self.num_players == 4 and len(self.play_order) in (1, 3) ) :
            self.play_order.append(None)

        self.play_order.append(player)
        self.getTurnLog(player).play_order = len(self.play_order)

        if self.num_players == 5 and len(self.play_order) == 5 :
            self.play_order.append(None)

    def reset_renaissance_usage(self):
        for key in self.renaissance_usage:
            self.renaissance_usage[key] = False

    def get_next_renaissance_player(self, player=None):
        if player == None :
            # find first player who can use renaissance
            from_idx = 0
        else :
            # find next player who can use renaissance
            from_idx = self.play_order.index( player ) + 1

        for i in range(from_idx, 6):
            user_id = self.play_order[i]
            if user_id != None \
                and user_id in self.renaissance_usage.keys() \
                and self.renaissance_usage[ user_id ] == False :
                    # Renaissance 를 연구하고, 아직 사용하지 않은 player
                    p_player = self.get_prev_player(user_id, include_chaos=True)
                    n_player = self.get_next_player(user_id, include_chaos=True)
                    if ( p_player != None and p_player not in self.renaissance_usage.keys() ) \
                        or ( n_player != None and n_player not in self.renaissance_usage.keys() ) :
                        return user_id
        return None

    def get_next_buy_card_player(self, player=None):
        if player == None :
            # find first player who can use renaissance
            from_idx = 0
        else :
            # find next player who can use renaissance
            from_idx = self.play_order.index( player ) + 1

        for i in range(from_idx, 6):
            user_id = self.play_order[i]
            if user_id != None :
                h = self.getHouseInfo(user_id)
                if 'P' in h.advances.keys() or 'V' in h.advances.keys() :
                    return user_id
        return None

    def get_prev_player(self, player=None, include_chaos=False):
        if player == None:
            # find last player
            from_idx = 5
        else :
            # find prev player
            from_idx = self.play_order.index( player ) - 1

        for i in range(from_idx, -1, -1):
            user_id = self.play_order[i]
            if user_id != None and ( include_chaos or self.getHouseInfo(user_id).chaos_out == False ) :
                return user_id
        return None

    def get_next_player(self, player=None, include_chaos=False):
        if player == None:
            # find first player
            from_idx = 0
        else :
            # find next player
            from_idx = self.play_order.index( player ) + 1

        for i in range(from_idx, 6):
            user_id = self.play_order[i]
            if user_id != None and ( include_chaos or self.getHouseInfo(user_id).chaos_out == False ) :
                return user_id
        return None

    def get_last_moving_watermill_player(self):
        for i in range(5, -1, -1):
            if self.play_order[i] != None:
                h = self.getHouseInfo(self.play_order[i])
                if 'K' in h.advances.keys() :
                    return self.play_order[i]
        return None

    def shuffle_cards(self, method, params):
        rand_dict = params['random'] if 'random' in params.keys() else {}
        cards = []
        edition = Edition.objects.filter(name__exact=self.edition)

        if method == GameInfo.SHUFFLE_NEXT_EPOCH :
            self.epoch += 1

        if self.epoch == 4 :
            self.final_turn = True
            return []

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
            elif method == GameInfo.SHUFFLE_NEXT_EPOCH :
                hcards = HistoryCard.objects                    \
                            .filter(edition__exact=edition)     \
                            .filter(epoch__exact=self.epoch)
                for c in hcards:
                    cards.append(c.short_name)
            random.shuffle(cards)

        self.draw_stack = cards
        if method != GameInfo.SHUFFLE_TURN2 :
            self.discard_stack = []
        return list(self.draw_stack)

    def get_province(self, province_name):
        if province_name not in self.provinces:
            raise GameInfo.ProvinceNotFound("'" + province_name  + "' is not a valid province name.")
        return self.provinces[province_name]

    def add_tokens(self, province_name, user_id, num_tokens, from_expansion=True, colored=False):
        p = self.get_province(province_name)
        edition = Edition.objects.filter(name__exact=self.info.edition)
        p_info = Province.objects.filter(edition=edition, short_name=province_name)

        if "color-marker" in p or "white-marker" in p : 
            raise GameInfo.ConflictOccurs( "Dominance marker exists" )

        all_tokens = 0
        for i in ("color-token", "white-token"):
            if i in p:
                for k in p[i]:
                    all_tokens += p[i][k]
        
        if all_tokens + num_tokens > p_info.market_size :
            raise GameInfo.ConflictOccurs(  \
                    "market: " + str(p_info.market_size) + ", " + \
                    "current: " + str(all_tokens) + ", " + \
                    "new: " + str(num_tokens) )

        h = self.getHouseInfo(user_id)
        k = "white-token" if colored == False else "color-token"

        if from_expansion == True :
            if h.expansion_tokens < num_tokens:
                raise GameInfo.NotEnoughTokens( "You have only " + str(h.expansion_tokens) + " tokens" )
            h.expansion_tokens -= num_tokens
        else:
            if h.stock_tokens < num_tokens:
                raise GameInfo.NotEnoughTokens( "You have only " + str(h.stock_tokens) + " tokens" )
            h.stock_tokens -= num_tokens

        if h.user_id not in p[k]:
            p[k][h.user_id] = 0
        p[k][h.user_id] += num_tokens

    def remove_tokens(self, province_name):
        p = self.get_province(province_name)
        if "color-token" in p:
            for k in p["color-token"]:
                h = getHouseInfo(k)
                h.stock_tokens += p["color-token"][k]
            del p["color-token"]

        if "white-token" in p:
            for k in p["white-token"]:
                h = getHouseInfo(k)
                h.stock_tokens += p["white-token"][k]
            del p["white-token"]

    def set_marker(self, province_name, user_id, colored=False):
        self.remove_marker(province_name)
        self.remove_tokens(province_name)

        p = self.get_province(province_name)
        h = self.getHouseInfo(user_id)
        k = "white-marker" if colored == False else "color-marker"

        if h.dominance_marker == 0 :
            raise GameInfo.NotEnoughDominanceMarker("No dominance marker left")

        p[k] = h.user_id
        h.dominance_marker -= 1

    def remove_marker(self, province_name):
        p = self.get_province(province_name)

        if "color-marker" in p: 
            h = self.getHouseInfo(p["color-marker"])
            h.dominance_marker += 1
            del p["color-marker"]

        if "white-marker" in p:
            h = self.getHouseInfo(p["white-marker"])
            h.dominance_marker += 1
            del p["white-marker"]

    def add_marker_removal(self, province_name):
        p = self.get_province(province_name)

        if "color-marker" in p:
            h = self.getHouseInfo(p["color-marker"])
            if h.user_id not in self.marker_removal:
                self.marker_removal[h.user_id] = []
            self.marker_removal[h.user_id].append(province_name)
        else:
            raise MarkerNotFound("No dominance marker found on '" + province_name + "'")

    def resolve_marker_removal(self):
        for n in self.info.marker_removal:
            h = self.info.getHouseInfo(n)
            if len(self.info.marker_removal[n]) <= h.stock_tokens:
                for p in self.info.marker_removal[n]:
                    self.info.remove_marker(p)
                    self.info.add_tokens(p, n, 1, from_expansion=False, colored=True)
                del self.info.marker_removal[n]

        player = get_next_player_for_marker_removal()
        if player != None:
            self.info.state = player + '.' + GameInfo.REMOVE_MARKER + '.' + self.info.state

    def get_next_player_for_marker_removal(self):
        if self.info.marker_removal:
            for key in self.info.play_order:
                if key in self.info.marker_removal:
                    return key
        return None

    def clear_marker_removal(self):
        self.marker_removal = {}

    def epoch1_ma_voided(self):
        for e in range(1, 4) :
            for c in ('E18_gun', 'E19_bow'):
                if c in self.info.card_log['epoch_' + str(e)] :
                    return True
        return False

    def get_accessible_provinces(self, include_overland_east=True, include_far_east=True, include_new_world=True):
        edition = Edition.objects.filter(name=self.edition)
        provinces = Province.objects.all()
        if self.num_players < 6 :
            provinces = provinces.exclude(area=AREA_I)
        if self.num_players < 5 :
            provinces = provinces.exclude(area=AREA_II)
        if self.num_players < 4 :
            provinces = provinces.exclude(area=AREA_III)
        if include_overland_east == False :
            provinces = provinces.exclude(area=AREA_VI)
        if include_far_east == False :
            provinces = provinces.exclude(area=AREA_FAR_EAST)
        if include_new_world == False :
            provinces = provinces.exclude(area=AREA_NEW_WORLD)

        return provinces

    class ProvinceNotFound(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class HouseNotFound(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class MarkerNotFound(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class NotEnoughTokens(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class NotEnoughDominanceMarker(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class ConflictOccurs(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

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
    PRE_PHASE       =   'pre_phase'
    POST_PHASE      =   'post_phase'
    DEAL_CARDS      =   'deal_cards'
    DISCARD         =   'discard'
    BID             =   'bid'
    CHOOSE          =   'choose'
    DETERMINE_ORDER =   'determine_order'
    PLAY_CARD       =   'play_card'
    PASS            =   'pass'
    RESOLVE_WAR     =   'resolve_war'

    class InvalidParameter(Exception):
        def __init__(self, message):
            self.message = message
        def __unicode__(self):
            return repr(self.message)

    class WarNotResolved(Exception):
        def __init__(self, message, actions=[]):
            self.message = message
            self.actions = actions
        def __unicode__(self):
            return repr(self.message)

def split_state_string(state):
    state_part = state.split('.', 2)
    if len(state_part) == 2:
        state_part.append(None)
    return state_part

class GameState(object):
    ALL             =   'all'
    AUTO            =   'auto'

    INITIALIZE              =   'init'
    HOUSE_BIDDING           =   'housebidding'
    CHOOSE_CAPITAL          =   'choose_capital'
    TOKEN_BIDDING           =   'token_bidding'
    TIE_BREAKING            =   'tie_breaking'
    DRAW_CARD               =   'draw_card'
    BUY_CARD                =   'buy_card'
    PLAY_CARD               =   'play_card'
    POST_WAR                =   'post_war'
    RESOLVE_CIVIL_WAR       =   'resolve_civil_war'
    REMOVE_MARKER           =   'remove_marker'
    APPLY_RENAISSANCE       =   'apply_renaissance'
    APPLY_WATERMILL         =   'apply_watermill'
    REMOVE_SURPLUS_SHORTAGE =   'remove_shortage_surplus'
    PURCHASE                =   'purchase'

    STATE_MAPS = {
        INITIALIZE              : 'InitState',
        HOUSE_BIDDING           : 'HouseBiddingState',
        CHOOSE_CAPITAL          : 'ChooseCapitalState',
        TOKEN_BIDDING           : 'TokenBiddingState',
        TIE_BREAKING            : 'TieBreakingState',
        DRAW_CARD               : 'DrawCardsState',
        BUY_CARD                : 'BuyCardsState',
        PLAY_CARD               : 'PlayCardsState',
        POST_WAR                : 'PostWarState',
        RESOLVE_CIVIL_WAR       : 'ResolveCivilWarState',
        REMOVE_MARKER           : 'RemoveMarkerState',
        APPLY_RENAISSANCE       : 'ApplyRenaissanceState',
        APPLY_WATERMILL         : 'ApplyWatermillState',
        REMOVE_SURPLUS_SHORTAGE : 'RemoveSurplusShortageState',
        PURCHASE                : 'PurchaseState',
    }

    def __init__(self, info, actor='all', depends_on=None):
        self.info = info
        self.actor = actor
        self.depends_on = depends_on

    def action(self, a, user_id=None, params={}):
        raise GameState.NotSupportedAction(
                    type(self).__name__ + '( ' + str(self.actor) + ', ' + str(self.depends_on) 
                    + ' ) cannot handle ' + a) 

    @staticmethod
    def getInstance(info):
        (actor, name, remains) = split_state_string( info.state )
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
            rand_dict = {}
            rand_dict['draw_stack'] = self.info.shuffle_cards(GameInfo.SHUFFLE_INIT, params)

            response = {}

            for h in self.info.house_bidding_log:
                h.draw_cards.append(self.info.draw_stack.pop())
                h.draw_cards.append(self.info.draw_stack.pop())
                h.draw_cards.append(self.info.draw_stack.pop())

            edition = Edition.objects.filter(name__exact=self.info.edition)
            all_provinces = self.info.get_accessible_provinces()
            for p in all_provinces:
                self.info.provinces[p.short_name] = { }

            self.info.state = GameState.ALL + '.' + GameState.HOUSE_BIDDING
            response['random'] = rand_dict

            return response
        else:
            return super(InitState, self).action(a, params)

def cmp_house_bid(x, y):
    diff = x.bid - y.bid
    i = 0
    while diff == 0 and i < len(x.dice_rolled) and i < len(y.dice_rolled) : 
        diff = x.dice_rolled[i] - y.dice_rolled[i]
        i += 1
    return diff

def cmp_play_order_before_tie_break(info):
    def inner(player_x, player_y, info=info):
        turn = info.turn
        bid_x = info.getTurnLog( player_x ).tokens
        bid_y = info.getTurnLog( player_y ).tokens
        diff = bid_x - bid_y
        if diff == 0 :
            diff = info.get_house_choice_order(player_y) - info.get_house_choice_order(player_x)
        return diff
    return inner

def cmp_play_order_after_tie_break(info):
    def inner(player_x, player_y, info=info):
        turn = info.turn
        bid_x = info.getTurnLog( player_x ).tokens
        bid_y = info.getTurnLog( player_y ).tokens
        diff = bid_x - bid_y
        if diff == 0 :
            tie_break = info.play_order_tie_break
            tb_x = tie_break['order_choice'][player_x]
            tb_y = tie_break['order_choice'][player_y]
            diff = tb_x - tb_y
        return diff
    return inner

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
                # 이미 sort 되어 있으므로, single-loop 로 가능하다.
                for i in range(len(self.info.house_bidding_log)-1):
                    if cmp_house_bid(self.info.house_bidding_log[i], self.info.house_bidding_log[i+1]) == 0 :
                        roll[i] = True
                        roll[i+1] = True
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
                raise GameState.InvalidAction( "Not user '" + user_id + "' turn")
            if 'choice' not in params.keys() :
                raise Action.InvalidParameter(Action.CHOOSE + " requires 'choice' parameter.")

            choice = params['choice']
            response = {}

            available = list(GameInfo.HOUSES[0:self.info.num_players])
            for key in self.info.houses.keys():
                h = self.info.getHouseInfo(key)
                available.remove(h.house_name)

            if choice not in available:
                raise Action.InvalidParameter("'" + choice + "' is already chosen or not allowed.")

            bidinfo = self.info.house_bidding_log[len(self.info.houses)]

            h = HouseInfo(
                    house_name=choice,
                    user_id=user_id,
                    hands = list(bidinfo.draw_cards),
                    cash = 40 - bidinfo.bid,
            )
            self.info.houses[user_id] = h
            self.info.set_marker(choice, user_id, colored=True)

            # 마지막 플레이어만 남았다면 자동으로 남은 수도를 선택하도록 함
            available.remove(choice)
            if len(available) == 1:
                response['queue_action'] = { 
                    'action': Action.CHOOSE, 
                    'choice': available[0], 
                    '_player': self.info.house_bidding_log[len(self.info.houses)].user_id,
                    }

            if len(self.info.houses) < self.info.num_players:
                self.info.state = self.info.house_bidding_log[len(self.info.houses)].user_id \
                                    + '.' + GameState.CHOOSE_CAPITAL
            else:
                self.info.state = GameState.ALL + '.' + GameState.TOKEN_BIDDING
                response['queue_action'] =  { 'action': Action.PRE_PHASE } 
                self.info.epoch = 1
                self.info.turn = 1
                for key in self.info.houses:
                    self.info.getHouseInfo(key).prepare_new_turn(self.info.turn)

            return response
        else:
            return super(ChooseCapitalState, self).action(a, params)

class TokenBiddingState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.PRE_PHASE :
            # TODO turn counter 증가 및 TurnLog 추가는 Turn 종료시에 한다.
            self.info.prepare_new_turn()
            return {}
        elif a == Action.POST_PHASE :
            for key in self.info.houses:
                h = self.info.getHouseInfo(key)
                l = h.turn_logs[self.info.turn - 1]
                h.cash = l.cash - abs(l.tokens)

                h.expansion_tokens = l.tokens
                if h.expansion_tokens < 0 :
                    h.expansion_tokens = 0
                if h.expansion_tokens > h.stock_tokens:
                    h.expansion_tokens = h.stock_tokens
                h.stock_tokens -= h.expansion_tokens

            self.info.state = GameState.ALL + '.' + GameState.DRAW_CARD
            return { 'queue_action':  { 'action': Action.PRE_PHASE } }
        elif a == Action.BID :
            if user_id == None :
                raise Action.InvalidParameter(Action.BID + " requires 'used_id'")
            if 'bid' not in params.keys() :
                raise Action.InvalidParameter(Action.BID + " requires 'bid' parameter.")
            hinfo = self.info.getHouseInfo(user_id)
            turn_log = hinfo.turn_logs[ self.info.turn - 1 ]
            turn_log.tokens = int(params['bid'])

            # preceed to determine order ? 
            bidding_complete = True
            for key in self.info.houses:
                hinfo = self.info.getHouseInfo(key)
                if hinfo.turn_logs[ self.info.turn - 1 ].tokens == None:
                    bidding_complete = False
                    break

            response = {}
            if bidding_complete == True:
                response['queue_action'] = { 'action': Action.DETERMINE_ORDER }

            return response
        elif a == Action.DETERMINE_ORDER :
            p_list = list(self.info.houses.keys())

            tie_break = self.info.play_order_tie_break
            if not tie_break:
                p_list.sort(cmp=cmp_play_order_before_tie_break(self.info))
                for i in range(len(p_list) - 1):
                    if self.info.getTurnLog( p_list[i] ).tokens == self.info.getTurnLog( p_list[i+1] ).tokens :
                        # Tie breaking required
                        self.info.clear_play_order()

                        tie_break = { 'resolve_order': [], 'ties': {}, 'order_choice': {}}
                        for n in range(len(p_list)):
                            bid = str(self.info.getTurnLog( p_list[n] ).tokens)
                            if bid not in tie_break['ties'].keys() :
                                tie_break['ties'][ bid ] = []
                            tie_break['ties'][ bid ].append( p_list[n] )
                            tie_break['resolve_order'].append( p_list[n] )

                        for k in tie_break['ties']:
                            if len(tie_break['ties'][k]) == 1 :
                                tie_break['resolve_order'].remove( tie_break['ties'][k][0] )

                        self.info.play_order_tie_break = tie_break
                        self.info.state = tie_break['resolve_order'][0] + '.' + GameState.TIE_BREAKING \
                                        + '.' + GameState.ALL + '.' + GameState.TOKEN_BIDDING
                        return {}

                    self.info.append_play_order( p_list[i] )

                # Here, len(p_list) == 1 
                self.info.append_play_order( p_list[len(p_list)-1] )
            else : # after tie break
                p_list.sort(cmp=cmp_play_order_after_tie_break(self.info))
                for p in p_list:
                    self.info.append_play_order( p )
                
            self.info.play_order_tie_break = {}
            return { 'queue_action': { 'action': Action.POST_PHASE } }
        else:
            return super(TokenBiddingState, self).action(a, params)

class TieBreakingState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.CHOOSE:
            if user_id != self.actor :
                raise GameState.InvalidAction( "Not user '" + user_id + "' turn")
            if 'choice' not in params.keys() :
                raise Action.InvalidParameter(Action.CHOOSE + " requires 'choice' parameter.")

            choice = int(params['choice'])
            tie_break = self.info.play_order_tie_break
            bid = str(self.info.getTurnLog( user_id ).tokens)
            response = {}

            possible_choice = range(1, len(tie_break['ties'][bid]) + 1)
            for k in tie_break['ties'][bid]:
                if k in tie_break['order_choice'] :
                    possible_choice.remove(tie_break['order_choice'][k])

            if choice not in possible_choice :
                raise Action.InvalidParameter("invalid 'choice' value" + str(choice))

            tie_break['order_choice'][user_id] = choice
            tie_break['resolve_order'].remove(user_id)
            possible_choice.remove(choice)

            if tie_break['resolve_order'] :
                self.info.play_order_tie_break = tie_break
                self.info.state = tie_break['resolve_order'][0] + '.' + GameState.TIE_BREAKING \
                                + '.' + GameState.ALL + '.' + GameState.TOKEN_BIDDING
                if len(possible_choice) == 1 :
                    response['queue_action'] = { 
                        'action': Action.CHOOSE, 
                        'choice': possible_choice[0], 
                        '_player': tie_break['resolve_order'][0],
                        }
            else:
                response['queue_action'] = { 'action': Action.DETERMINE_ORDER }
                self.info.state = GameState.ALL + '.' + GameState.TOKEN_BIDDING

            return response
        else:
            return super(TieBreakingState, self).action(a, params)

class DrawCardsState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.PRE_PHASE :
            response = {}
            rand_dict = {}
            if self.info.turn == 1 :
                rand_dict['draw_stack'] = self.info.shuffle_cards(GameInfo.SHUFFLE_TURN1, params)
            elif self.info.turn == 2 and self.info.num_players in (5, 6) :
                rand_dict['draw_stack'] = self.info.shuffle_cards(GameInfo.SHUFFLE_TURN2, params)
           
            response['random'] = rand_dict
            self.info.reset_renaissance_usage()
            next_state = ''
        
            next_renaissance_player = self.info.get_next_renaissance_player() 
            if next_renaissance_player != None :
                next_state += next_renaissance_player + '.' + GameState.APPLY_RENAISSANCE + '.'

            if self.info.shortage or self.info.surplus : 
                next_state += self.info.get_next_player() + '.' + GameState.REMOVE_SURPLUS_SHORTAGE + '.'

            watermill_player = self.info.get_last_moving_watermill_player()
            if watermill_player != None:
                next_state += watermill_player + '.' + GameState.APPLY_WATERMILL + '.'

            next_state += GameState.AUTO + '.' + GameState.DRAW_CARD

            (actor, name, remains) = split_state_string( next_state )

            if actor == GameState.AUTO and name == GameState.DRAW_CARD:
                response['queue_action'] = { 'action': Action.DEAL_CARDS }
            self.info.state = next_state

            return response

        elif a == Action.POST_PHASE :
            self.info.state = GameState.AUTO + '.' + GameState.BUY_CARD
            return { 'queue_action' :  { 'action': Action.PRE_PHASE } }

        elif a == Action.DEAL_CARDS :
            rand_dict = {}
            response = {}

            for key in self.info.play_order:
                if key == None: 
                    continue
                h = self.info.getHouseInfo(key)

                if not self.info.draw_stack :
                    rand_dict['draw_stack'] = self.info.shuffle_cards(GameInfo.SHUFFLE_NEXT_EPOCH, params)
                    if self.info.final_turn == True :
                        del rand_dict['draw_stack']
                        break

                h.hands.append(self.info.draw_stack.pop())

            if rand_dict :
                response['random'] = rand_dict

            response['queue_action'] = { 'action': Action.POST_PHASE }

            return response
        return super(DrawCardsState, self).action(a, params)

class ApplyRenaissanceState(GameState):
    ''' play order change w/ [Q] Renaissance advance '''
    def action(self, a, user_id=None, params={}):
        return super(ApplyRenaissanceState, self).action(a, params)

class RemoveSurplusShortageState(GameState):
    ''' removal shortage/surplus by 1st player '''
    def action(self, a, user_id=None, params={}):
        return super(RemoveSurplusShortageState, self).action(a, params)

class ApplyWatermillState(GameState):
    ''' adjust shortage/surplus of Grain, Cloth, Wine or Metal w/ [K] Wind/WaterMill advance '''
    def action(self, a, user_id=None, params={}):
        return super(ApplyWatermillState, self).action(a, params)

class BuyCardsState(GameState):
    ''' buy card w/ [V] or discard card w/ [P] '''
    def action(self, a, user_id=None, params={}):
        if a == Action.PRE_PHASE :
            response = {}

            buy_card_player = self.info.get_next_buy_card_player()
            if buy_card_player == None :
                response['queue_action'] = { 'action': Action.POST_PHASE }
            else :
                next_state = buy_card_player + '.' + GameState.BUY_CARD

                if self.info.get_next_buy_card_player( buy_card_player ) != None :
                    # 두 명 이상이 행동을 할 수 있으므로, renaissance 사용 확인이 필요하다.
                    next_renaissance_player = self.info.get_next_renaissance_player() 
                    if next_renaissance_player != None :
                        next_state = next_renaissance_player + '.' + GameState.APPLY_RENAISSANCE + '.' + next_state
                self.info.state = next_state

            return response
        elif a == Action.POST_PHASE :
            self.info.state = GameState.ALL + '.' + GameState.PLAY_CARD
            return { 'queue_action' :  { 'action': Action.PRE_PHASE } }
        return super(BuyCardsState, self).action(a, params)

class PlayCardsState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.PRE_PHASE :
            response = {}
            next_state = ''

            next_renaissance_player = self.info.get_next_renaissance_player() 
            if next_renaissance_player != None :
                next_state += next_renaissance_player + '.' + GameState.APPLY_RENAISSANCE + '.'

            next_state += self.info.get_next_player() + '.' + GameState.PLAY_CARD

            self.info.state = next_state

            return response
        elif a == Action.POST_PHASE :
            self.info.state = GameState.ALL + '.' + GameState.PURCHASE
            return { 'queue_action' :  { 'action': Action.PRE_PHASE } }
        elif a == Action.PASS:
            if user_id != self.actor :
                raise GameState.InvalidAction( "Not user '" + user_id + "' turn")
            if self.war_resolved() == False:
                raise Action.WarNotResolved( "'War!' must be resolved before pass." )

            response = {}
            next_player = self.info.get_next_player(self.actor)
            if next_player == None:
                response['queue_action'] = { 'action': Action.POST_PHASE }
            else :
                self.info.state = next_player + '.' + GameState.PLAY_CARD
            return response
        elif a == Action.PLAY_CARD:
            if 'card' not in params.keys() :
                raise Action.InvalidParameter(Action.PLAY_CARD + " requires 'card' parameter.")
            if user_id != self.actor :
                raise GameState.InvalidAction( "Not user '" + user_id + "' turn")
            if self.war_resolved() == False and card not in ('E12_arm', 'E18_gun', 'E19_bow', 'E27_sti'):
                raise Action.WarNotResolved( "'War!' must be resolved before play other card." )

            card = params['card']

            h = self.info.getHouseInfo(user_id)
            if card not in h.hands:
                raise Action.InvalidParameter("You don't have '" + card + "'")

            if card[0] == 'C':
                response = self.play_commodity_card(card, params)
            elif card[0] == 'L':
                response = self.play_leader_card(card, user_id)
            else :
                response = self.play_event_card(card, user_id, params)

            h.hands.remove(card)
            self.info.discard_stack.append(card)

            return response

        elif a == Action.RESOLVE_WAR:
            # Each player rolls 1 die. 
            # [W] Nationalism & Military Advantages modify their owner's die roll by +1 (each). 
            # Highest total gains one Misery, lowest total gains two Misery. 
            # The difference between the modified die rolls is the amount of supportable 
            # Colored Dominance Markers (circles) the loser must cede to the winner (loser's choice). 
            # If tied, both sides gain one Misery and continue resolution in each succeeding round of 
            # the Play Cards Phase until one side wins.                                 
            # 
            # 참고
            # http://boardgamegeek.com/thread/1125054/military-advantages-stacking
            # http://boardgamegeek.com/thread/514950/again-war-card
            # http://boardgamegeek.com/thread/299484/war-card
            response = {}
            rand_dict = params['random'] if 'random' in params.keys() else {}

            if 'attacker' not in rand_dict:
                rand_dict['attacker'] = roll_dice()

            if 'defender' not in rand_dict:
                rand_dict['defender'] = roll_dice()

            mod = {}
            mod[self.info.war['attacker']] = rand_dict['attacker'] 
            mod[self.info.war['defender']] = rand_dict['defender'] 

            for p in mod:
                h = self.info.getHouseInfo(p)
                if 'W' in h.advances:
                    mod[p] += 1

            has_lg = { self.info.war['attacker'] : False, self.info.war['defender'] : False }
            has_ma = { self.info.war['attacker'] : False, self.info.war['defender'] : False }

            if self.info.gunpowder in mod:
                has_lg[self.info.gunpowder] = True
                has_ma[self.info.gunpowder] = True
                mod[self.info.gunpowder] += 1

            if self.info.longbow in mod:
                has_lg[self.info.longbow] = True
                has_ma[self.info.gunpowder] = True
                mod[self.info.longbow] += 1

            if self.info.stirrups == self.info.war['attacker'] and has_lg[self.info.war['defender']] == False :
                mod[self.info.war['attacker']] += 1
                has_ma[self.info.war['attacker']] = True

            if self.info.armor == self.info.war['attacker'] and has_lg[self.info.war['defender']] == False :
                mod[self.info.war['attacker']] += 1
                has_ma[self.info.war['attacker']] = True

            if self.info.stirrups == self.info.war['defender'] and has_lg[self.info.war['attacker']] == False :
                mod[self.info.war['defender']] += 1
                has_ma[self.info.war['defender']] = True

            if self.info.armor == self.info.war['defender'] and has_lg[self.info.war['attacker']] == False :
                mod[self.info.war['defender']] += 1
                has_ma[self.info.war['defender']] = True

            self.info.war['last_rolled_state'] = self.info.state
            if has_ma[self.info.war['attacker']] == False \
                and mod[self.info.war['attacker']] == mod[self.info.war['defender']] :
                # 비김 
                self.info.getHouseInfo(self.info.war['attacker']).adjust_misery(1)
                self.info.getHouseInfo(self.info.war['defender']).adjust_misery(1)
            else :
                # 어느 한 쪽의 승리
                if mod[self.info.war['attacker']] >= mod[self.info.war['defender']]:
                    # MA가 있어야 mod 값이 같은 경우에 이 곳에 진입할 수 있으므로, 
                    # 여기에서는 >= 로 비교해도 충분하다. 
                    self.info.war['winner'] = self.info.war['attacker']
                    self.info.war['loser'] = self.info.war['defender']
                else :
                    self.info.war['winner'] = self.info.war['defender']
                    self.info.war['loser'] = self.info.war['attacker']

                self.info.getHouseInfo(self.info.war['winner']).adjust_misery(1)
                self.info.getHouseInfo(self.info.war['loser']).adjust_misery(2)
                self.info.war['difference'] = mod[self.info.war['winner']] - mod[self.info.war['loser']]
                self.info.war['available_provinces'] = []
                if self.info.war['difference'] == 0 :
                    self.info.reset_war_info()
                else :
                    h_winner = self.info.getHouseInfo(self.info.war['winner'])
                    h_loser = self.info.getHouseInfo(self.info.war['loser'])
                    p_list = []
                    for key in self.info.provinces:
                        p = self.info.provinces[key]
                        if p['color-marker'] == h_winner.user_id : 
                            p_list.append(key)

                    accessible_p_list = self.info.get_accessible_provinces(
                                            include_overland_east= 'R' in h_winner.advances, 
                                            include_far_east= 'T' in h_winner.advances, 
                                            include_new_world= 'U' in h_winner.advances
                    )

                    self.info.war['available_provinces'] = list(set(p_list).intersection(set(accessible_p_list)))
                    if len(self.info.war['available_provinces']) <= self.info.war['difference'] :
                        # 넘겨줄 수 있는 province가 넘겨주어야 하는 province 보다 적거나 같으면
                        # 그 province들만 모두 넘겨주고 상황을 종료한다. 
                        for p in self.info.war['available_provinces'] :
                            self.info.set_marker(p, self.info.war['winner'], colored=True)
                        self.info.reset_war_info()
                    else:
                        self.info.state = self.info.war['loser'] + '.' + GameState.POST_WAR + '.' + self.info.state

            response['random'] = rand_dict
            return response
        return super(PlayCardsState, self).action(a, params)

    def war_resolved(self):
        last_state = self.info.war['last_rolled_state']
        if last_state == None or last_state == self.info.state :
            return True
        return False

    def play_commodity_card(self, card, params):
        response = {}
        edition = Edition.objects.filter(name=self.info.edition)
        commodity_card = CommodityCard.objects.get(edition=edition, short_name=card)
        if ( len(commodity_card.commodities.all()) > 1 ) :
            if 'choice' not in params.keys() :
                raise Action.InvalidParameter("'" + str(commodity_card) + "' requires 'choice' parameter.")
            choice = params['choice']

            try:
                if len(choice) == 2 :
                    commodity = commodity_card.commodities.get(short_name=choice)
                else:
                    commodity = commodity_card.commodities.get(full_name=choice)
            except (Commodity.DoesNotExist) as e:
                raise Action.InvalidParameter("'choice' parameter must be either '" + str(commodity_card) + "'")
        else :
            commodity = commodity_card.commodities.all()[0]
        provinces = Province.objects.filter(edition=edition, commodities=commodity)

        owners = {}
        for p in provinces:
            if p.short_name in self.info.provinces and "color-marker" in self.info.provinces[p.short_name] :
                owner = self.info.provinces[p.short_name]["color-marker"]
                if owner not in owners:
                    owners[owner] = 0
                owners[owner] += 1

        for key in owners:
            income = owners[key] * owners[key] * commodity.unit_price
            h = self.info.getHouseInfo(key)
            l = self.info.getTurnLog(key)
            l.card_income += income
            h.cash += income

        self.info.card_log['epoch_' + str(self.info.epoch)][card] = str(self.info.epoch) + "." + str(self.info.turn)
        return response

    def play_leader_card(self, card, user_id):
        response = {}
        edition = Edition.objects.filter(name=self.info.edition)
        leader_card = LeaderCard.objects.get(edition=edition, short_name=card)

        h = self.info.getHouseInfo(user_id)
        l = self.info.getTurnLog(user_id)
        if 'O' in h.advances:
            credit = leader_card.discount
            if leader_card.short_name == 'L15_R' and self.info.crusades != None:
                credit = leader_card.discount_on_event
            elif leader_card.short_name == 'L25_RY' and self.info.mongol_armies == True:
                credit = leader_card.discount_on_event

            for a in leader_card.advances.all():
                if a.short_name in h.advances:
                    l.card_income += income
                    h.cash += income

        self.info.leader.stack.append(card)
        self.info.leader.player[card] = user_id
        self.info.leader.play_log[card] = self.info.turn
        return response

    def play_event_card(self, card, user_id, params):
        response = {}

        if card == 'E11_A' :
            # A player of your choice may pay half of written cash to Banker. Penalty cannot exceed current cash. 
            # Cash already spent on Patronage defense is not vulnerable. Voided by LAWS OF MATTER. 
            # If all players have LAWS OF MATTER, this card becomes unplayable Misery burden.                                    
            if 'target' not in params.keys() :
                raise Action.InvalidParameter("'Alchemist's Gold' requires 'target' parameter.")
            if self.info.is_valid_player( params['target'] ) == False :
                raise Action.InvalidParameter("Player '" + params['target'] + "' is not in the game.")

            h = self.info.getHouseInfo(params['target'])
            if 'C' in h.advances.keys() or self.info.enlightened_ruler == params['target'] :
                raise Action.InvalidParameter( \
                        "You cannot play 'Alchemist's Gold' on player '" + params['target'] + "'."
                )

            l = self.info.getTurnLog(params['target'])
            wc = l.written_cash()
            penalty = ( wc + 1 ) / 2 # 0.5 는 반올림하기 위해서, wc + 1 을 2로 나눔
            if penalty > h.cash : 
                penalty = h.cash

            h.cash -= penalty
            l.card_damage += penalty
        elif card =='E12_arm':
            # A temporary Arms advantage enhances your trading ventures. 
            # You win all Attack ties this turn (including WAR). 
            # Add 1 to your competition totals this turn on both offense and defense. Voided by LONG BOW or GUNPOWDER. 
            # If voided, ARMOR becomes unplayable Misery burden.                                 
            if self.info.epoch1_ma_voided() == True :
                raise Action.InvalidParameter("You cannot play 'Armor' any more.")
            self.info.armor = user_id
        elif card =='E13_B':
            # Select one Area to be hit by the plague. 
            # All Colored Tokens (squares) in that Area are returned to their respective Stocks. 
            # Then reduce all Colored Dominance Markers (circles) of all players in that Area 
            # to a single Colored Token (square) per Province.                                    
            if 'target' not in params.keys() :
                raise Action.InvalidParameter("'Black Death' requires 'target' parameter.")
            playable_area = [1, 2, 3, 4, 5, 6, 7, 8][6-self.info.num_players:]
            if params['target'] not in playable_area:
                raise Action.InvalidParameter("You cannot play 'Black Death' on Area " + params['target'] + ".")

            edition = Edition.objects.filter(name=self.info.edition)
            # token 부터 회수하고, dominance marker를 token으로 교환한다. 
            provinces = Province.objects                    \
                            .filter(edition=edition)        \
                            .filter(area=params['target'])  \
                            .order_by('market_size')

            self.info.clear_marker_removal()
            for p in provinces:
                try: 
                    self.info.add_marker_removal(p.short_name)
                except MarkerNotFound as e:
                    self.info.remove_tokens(p.short_name)

            self.info.resolve_marker_removal()
        elif card =='E14_C':
            # A player of your choice is struck by CIVIL WAR. He gains one Misery. 
            # Any Dominance Marker (circle) in his Capital is reduced to a Colored Token (square). 
            # He must lose his choice of half of his last recorded cash or half of his bid tokens (squares). 
            # At start of the Expansion Phase, his Order of play position becomes "last".                                  

            if 'target' not in params.keys() :
                raise Action.InvalidParameter("'Civil War' requires 'target' parameter.")
            if self.info.is_valid_player( params['target'] ) == False :
                raise Action.InvalidParameter("Player '" + params['target'] + "' is not in the game.")
            if self.info.enlightened_ruler == params['target'] :
                raise Action.InvalidParameter("You cannot play 'Civil War' on player '" + params['target'] + "'.")

            # 대상 플레이어가 토큰과 캐시 중 하나를 선택한 다음, 모든 값을 조정한다.
            self.info.state = params['target'] + '.' + GameState.RESOLVE_CIVIL_WAR + '.' + self.info.state
        elif card =='E15_cru':
            # Place one of your Colored Dominance Markers (circle) anywhere within Area VI 
            # and remove any other markers in that Province. Gain one Misery. 
            # This card increases the credits for WALTER THE PENNILESS if he is also played this turn. 
            # Voided by MONGOL ARMIES in Epoch 2 or Epoch 3 and becomes unplayable Misery burden.
            if self.info.mongol_armies == True :
                raise Action.InvalidParameter( "You cannot play 'The Crusades' any more.")

            if 'target' not in params.keys() :
                raise Action.InvalidParameter("'The Crusades' requires 'target' parameter.")

            edition = Edition.objects.filter(name=self.info.edition)
            province = Province.objects.get(edition=edition, short_name=params['target'])

            if province.area != AREA_VI:
                raise Action.InvalidParameter("'target' parameter must be the short name of a Province in Area VI.")

            h = self.info.getHouseInfo(user_id)
            self.info.set_marker(params['target'], user_id, colored=True)
            self.info.crusades = user_id
            h.adjust_misery(1)
        elif card =='E16_rul':
            # Play on yourself to void the effects of MYSTICISM, RELIGIOUS STRIFE, CIVIL WAR, 
            # REVOLUTIONARY UPRISINGS, REBELLION, and ALCHEMIST'S GOLD for the rest of the turn.
            self.info.enlightened_ruler = user_id
        elif card =='E17_fam':
            # All players gain four spaces on the Misery Index minus one space for each Grain Province they dominate. 
            # Having [J] Improved Agriculture also reduces the penalty by one space.                                  
            edition = Edition.objects.filter(name=self.info.edition)
            commodity = Commodity.objects.get(edition=edition, full_name='Grain')

            provinces = Province.objects.filter(edition=edition, commodities=commodity)

            grain_owners = {}
            for p in provinces:
                if "color-marker" in self.info.provinces[p.short_name] :
                    grain_owner = self.info.provinces[p.short_name]["color-marker"]
                    if grain_owner not in grain_owners:
                        grain_owners[grain_owner] = 0
                    grain_owners[grain_owner] += 1

            for key in self.info.houses:
                penalty = 4
                h = self.info.getHouseInfo(key)
                if 'J' in h.advances:
                    penalty -= 1
                if h in grain_owners:
                    penalty -= grain_owners[key]
                if penalty > 0:
                    h.adjust_misery(penalty)
        elif card =='E18_gun':
            # A temporary Arms advantage enhances your trading ventures. 
            # You win all Attack ties this turn (including WAR). 
            # Add 1 to all your competition totals this turn on both offense and defense. 
            # Voids ARMOR and STIRRUPS and turns them into Misery burdens.                                    
            self.info.gunpowder = user_id
        elif card =='E19_bow':
            # A temporary Arms advantage enhances your trading ventures. 
            # You win all Attack ties this turn (including WAR). 
            # Add 1 to all your competition totals this turn on both offense and defense 
            # except against players currently using GUNPOWDER. 
            # Voids ARMOR and STIRRUPS and turns them into Misery burdens.                                   
            self.info.longbow = user_id
        elif card =='E20_mys':
            # All players gain four spaces on the Misery Index minus one space for each Science Advance [A,B,C,D] held. 
            # This card becomes a worthless Misery burden if all players own all four Sciences [A,B,C,D]. 
            edition = Edition.objects.filter(name=self.info.edition)
            advances = Advanc.objects.filter(edition=edition).filter(category=Advance.SCIENCE)
            science_advances = []
            for a in advances:
                science_advances.append(a.ahort_name)
            science_advances_set = set(science_advances)
            sum_misery_level = 0

            for key in self.info.houses:
                h = self.info.getHouseInfo(key)
                if self.info.enlightened_ruler == h.user_id: 
                    continue
                dev_set = set(h.advances).intersection(science_advances_set)
                h.adjust_misery(len(science_advances_set) - len(dev_set))
                sum_misery_level += len(science_advances_set) - len(dev_set) 

            if sum_misery_level == 0 :
                # 본래는 GameInfo 데이터 변경 후에 exception을 내보내면 안되지만, 
                # 이 경우는 아무도 영향을 받지 않았으므로, 사실상 변경이 없는 셈이라 
                # exception을 발생해도 별 문제가 없다.
                raise Action.InvalidParameter( "You cannot play 'Mysticism Abounds' any more.")
        elif card =='E21_mon':
            # Collect $10 from the Bank. MARCO POLO credits are doubled if played hereafter. 
            # THE CRUSADES event becomes  unplayable Misery burden.                                  

            h = self.info.getHouseInfo(user_id)
            l = self.info.getTurnLog(user_id)

            h.cash += 10
            l.card_income += 10

            self.mongol_armies = True
        elif card =='E22_pap':
            # You may ban the acquisition by all players of any Advance in one of the following three categories: 
            #   Science [A,B,C,D], Religion [E,F,G,H] and Exploration [R,S,T,U]. 
            # Voided by RELIGIOUS STRIFE played in the same turn. 
            # When RELIGIOUS STRIFE occurs in Epoch 3, this card becomes an unplayable Misery burden.  
            if 'target' not in params.keys() :
                raise Action.InvalidParameter("'Papal Decree' requires 'target' parameter.")
            if params['target'] not in ( 'Science', 'Religion', 'Exploration' ):
                raise Action.InvalidParameter("'target' must be one of 'Science', 'Religion', 'Exploration'")
            if self.info.epoch == 3 and self.info.religious_strife == True:
                raise Action.InvalidParameter( "You cannot play 'Papal Decree' any more.")

            if self.info.religious_strife == True:
                # 이 때도 플레이는 가능하지만, 게임에는 아무런 영향을 미칠 수 없다 
                pass
            else:
                edition = Edition.objects.filter(name=self.info.edition)
                if params['target'] == 'Science':
                    advances = Advanc.objects   \
                                .filter(edition=edition) \
                                .filter(category=Advance.SCIENCE)
                elif params['target'] == 'Religion':
                    advances = Advanc.objects   \
                                .filter(edition=edition) \
                                .filter(category=Advance.RELIGION)
                else: # params['target'] == 'Exploration':
                    advances = Advanc.objects   \
                                .filter(edition=edition) \
                                .filter(category=Advance.EXPLORATION)
                self.papal_decree = []
                for a in advances:
                    self.papal_decree.append(a.short_name)
        elif card =='E23_vik':
            # Reduce any Dominance Marker (circle) to a Colored Token (square) in any coastal Province of your choice. 
            # If played during Epoch II, reduce two Colored Dominance Markers (circles). 
            # If played during Epoch III, reduce three Colored Dominance Markers (circles).                                 
            if 'targets' not in params.keys() :
                raise Action.InvalidParameter("'Pirates / Vikings' requires 'targets' parameter.")
            if isinstance(params['targets'], list) == False or len(params['targets']) != self.info.epoch :
                raise Action.InvalidParameter( \
                            "'targets' parameter must be an array of " + self.info.epoch + " Coastal Provinces"
                )

            edition = Edition.objects.filter(name=self.info.edition)
            self.info.clear_marker_removal()

            for key in params['targets']:
                p = Province.objects.get(edition=edition, short_name=key)
                self.info.add_marker_removal(p.short_name)
                if p.area == AREA_FAR_EAST or p.area == AREA_NEW_WORLD:
                    continue
                else:
                    w = Water.objects.filter(edition=edition, coast_of=p)
                    if len(w) == 0:
                        self.info.clear_marker_removal()
                        raise Action.InvalidParameter( \
                                "'targets' parameter must be an array of " + self.info.epoch + " Coastal Provinces"
                        )

            self.info.resolve_marker_removal()
        elif card =='E24_reb':
            # Local conflict occurs in any province of your choice except the New World and foreign capitals. 
            # Any Colored Dominance Marker (circle) in that province is reduced to a Colored Token (square).
            if 'target' not in params.keys() :
                raise Action.InvalidParameter("'Rebellion' requires 'target' parameter.")

            edition = Edition.objects.filter(name=self.info.edition)
            p = Province.objects.get(edition=edition, short_name=params['target'])

            if p.province_type == Province.CAPITAL or p.area == AREA_NEW_WORLD :
                raise Action.InvalidParameter("'target' cannot be a Capital or New World")

            p_info = self.get_province(p.short_name)

            if "color-marker" not in p_info or elf.info.enlightened_ruler == p_info["color-marker"] : 
                raise Action.InvalidParameter("You cannot play 'Rebellion' on '" + params['target'] + "'.")

            self.info.clear_marker_removal()
            self.info.add_marker_removal(p.short_name)
            self.info.resolve_marker_removal()
        elif card =='E25_rel':
            # All players increase Misery one space for each Religion Advance [E,F,G,H] they hold. 
            # Voids PAPAL DECREE, if played in the same turn. 
            # If played in Epoch 3, the PAPAL DECREE card becomes an unplayable Misery burden.                                 

            edition = Edition.objects.filter(name=self.info.edition)
            advances = Advanc.objects.filter(edition=edition).filter(category=Advance.RELIGION)
            religion_advances = []
            for a in advances:
                religion_advances.append(a.ahort_name)
            religion_advances_set = set(religion_advances)

            for key in self.info.houses:
                h = self.info.getHouseInfo(key)
                if self.info.enlightened_ruler == h.user_id: 
                    continue
                dev_set = set(h.advances).intersection(religion_advances_set)
                h.adjust_misery(len(dev_set))

            # Papal Decree가 선언되었다면 무효화시킨다.
            self.papal_decree = []
        elif card =='E26_rev':
            # Each player gains one space on the Misery Index for each Commerce Advance [I,J,K,L,M] he holds.
            edition = Edition.objects.filter(name=self.info.edition)
            advances = Advanc.objects.filter(edition=edition).filter(category=Advance.COMMERCE)
            commerce_advances = []
            for a in advances:
                commerce_advances.append(a.ahort_name)
            commerce_advances_set = set(commerce_advances)

            for key in self.info.houses:
                h = self.info.getHouseInfo(key)
                if self.info.enlightened_ruler == h.user_id: 
                    continue
                dev_set = set(h.advances).intersection(commerce_advances_set)
                h.adjust_misery(len(dev_set))
        elif card =='E27_sti':
            # A temporary Arms advantage enhances your trading ventures. 
            # You win all Attack ties this turn (including WAR). 
            # Add 1 to all your competition totals this turn on both offense and defense, 
            # except against player currently using ARMOR. 
            # Voided by LONG BOW or GUNPOWDER. If voided, STIRRUPS becomes unplayable Misery burden.
            if self.info.epoch1_ma_voided() == True :
                raise Action.InvalidParameter("You cannot play 'Stirrups' any more.")

            self.info.stirrups = user_id
        elif card =='E28_war':
            # Declare WAR on any player. Each player rolls 1 die. 
            # [W] Nationalism & Military Advantages modify their owner's die roll by +1 (each). 
            # Highest total gains one Misery, lowest total gains two Misery. 
            # The difference between the modified die rolls is the amount of supportable 
            # Colored Dominance Markers (circles) the loser must cede to the winner (loser's choice). 
            # If tied, both sides gain one Misery and continue resolution in each succeeding round of 
            # the Play Cards Phase until one side wins.                                 
            if 'target' not in params.keys() :
                raise Action.InvalidParameter("'War!' requires 'target' parameter.")
            if self.info.is_valid_player( params['target'] ) == False :
                raise Action.InvalidParameter("Player '" + params['target'] + "' is not in the game.")

            self.info.war['attacker'] = user_id
            self.info.war['defender'] = params['target']
            response['queue_action'] = { 'action': Action.RESOLVE_WAR, '_player': user_id }

        self.info.card_log['epoch_' + str(self.info.epoch)][card] = str(self.info.epoch) + "." + str(self.info.turn)
        return response

class PostWarState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.CHOOSE :
            if user_id != self.actor :
                raise GameState.InvalidAction( "Not user '" + user_id + "' turn")
            if 'choice' not in params.keys() :
                raise Action.InvalidParameter(Action.CHOOSE + " requires 'choice' parameter.")

            choice = params['choice']
            
            choice_refined = list(set(choice).intersection(set(self.info.war['available_provinces'])))

            if len(choice) != len(choice_refined) :
                raise Action.InvalidParameter("'choice' must contains cedible provinces only.")

            if len(choice_refined) != self.info.war['difference'] :
                raise Action.InvalidParameter("You must cede " +  str(self.info.war['difference']) + " provinces.")

            for p in choice_refined :
                self.info.set_marker(p, self.info.war['winner'], colored=True)
            self.info.reset_war_info()
            self.info.state = self.depends_on
        else :
            return super(PostWarState, self).action(a, params)
        return {}

class ResolveCivilWarState(GameState):
    def action(self, a, user_id=None, params={}):
        # A player of your choice is struck by CIVIL WAR. He gains one Misery. 
        # Any Dominance Marker (circle) in his Capital is reduced to a Colored Token (square). 
        # He must lose his choice of half of his last recorded cash or half of his bid tokens (squares). 
        # At start of the Expansion Phase, his Order of play position becomes "last".                                  
        if a == Action.CHOOSE :
            if user_id != self.actor :
                raise GameState.InvalidAction( "Not user '" + user_id + "' turn")
            if 'choice' not in params.keys() :
                raise Action.InvalidParameter(Action.CHOOSE + " requires 'choice' parameter.")
            if params['choice'] not in ('token', 'cash') :
                raise Action.InvalidParameter("'choice' parameter must be either 'token' or 'cash'")

            h = self.info.getHouseInfo(user_id)

            h.adjust_misery( 1 )
            if params['choice'] == 'token' :
                penalty = ( h.expansion_tokens + 1 ) / 2 # 0.5 는 반올림하기 위해서, wc + 1 을 2로 나눔
                h.stock_tokens += penalty
                h.expansion_tokens -= penalty
            else :
                l = self.info.getTurnLog(user_id)
                penalty = ( h.cash + 1 ) / 2 # 0.5 는 반올림하기 위해서, wc + 1 을 2로 나눔
                h.cash -= penalty
                l.card_damage += penalty
            
            capital = self.info.provinces[h.house_name]
            self.info.state = self.depends_on
            if 'color-marker' in capital:
                if capital['color-marker'] == h.house_name : 
                    # 수도를 보유하고 있음. 
                    # stock token 으로 채우거나, 비워둠
                    self.info.remove_marker(h.house_name)
                    if h.stock_tokens > 0 :
                        self.info.add_tokens(h.house_name, user_id, 1, from_expansion=False, colored=True)
                else :
                    # 수도를 점령당한 상태. 
                    # 점령중인 player가 결정해야 함
                    self.info.clear_marker_removal()
                    self.info.add_marker_removal(h.house_name)
                    self.info.resolve_marker_removal()
        else :
            return super(PostWarState, self).action(a, params)
        return {}

class RemoveMarkerState(GameState):
    def action(self, a, user_id=None, params={}):
        if a == Action.CHOOSE :
            if user_id != self.actor :
                raise GameState.InvalidAction( "Not user '" + user_id + "' turn")
            if 'choice' not in params.keys() :
                raise Action.InvalidParameter(Action.CHOOSE + " requires 'choice' parameter.")
            choice = params['choice']

            if type(choice) is not dict:
                raise Action.InvalidParameter("Invalid 'choice' parameter.")

            markers_to_remove = self.marker_removal[user_id]
            count = { 'empty' : 0, 'stock' : 0, 'expansion' : 0 }

            for key in choice:
                if key not in markers_to_remove:
                    raise Action.InvalidParameter("Dominance marker on '" + key + "' cannot be removed.")
                if choice[key] not in ('empty', 'stock', 'expansion'):
                    raise Action.InvalidParameter( \
                            "Dominance marker removal option must be either 'empty', 'stock' or 'expansion'."   \
                    )
                count[choice[key]] += 1

            h = self.info.getHouseInfo(user_id)
            if h.stock_tokens < count['stock']:
                raise Action.InvalidParameter(  \
                        "Not enough stock tokens; you have " + str(h.stock_tokens)  \
                        + ", required " + str(count['stock'])   \
                )

            if h.expansion_tokens < count['expansion']:
                raise Action.InvalidParameter(  \
                        "Not enough expansion tokens; you have " + str(h.expansion_tokens)  \
                        + ", required " + str(count['expansion'])   \
                )

            # all clear! 
            for key in choice: 
                self.info.remove_marker(key)
                if choice[key] == 'expansion':
                    self.info.add_tokens(h.house_name, user_id, 1, from_expansion=True, colored=True)
                elif choice[key] == 'stock':
                    self.info.add_tokens(h.house_name, user_id, 1, from_expansion=False, colored=True)
                self.marker_removal[user_id].remove(key)

            if len(self.marker_removal[user_id]) == 0:
                del self.marker_removal[user_id]
                player = get_next_player_for_marker_removal()
                if player != None:
                    self.info.state = player + '.' + GameInfo.REMOVE_MARKER + '.' + self.depends_on
                else: 
                    self.info.clear_marker_removal()
                    self.info.state = self.depends_on
        else :
            return super(RemoveMarkerState, self).action(a, params)
        return {}

class PurchaseState(GameState):
    def action(self, a, user_id=None, params={}):
        return super(PurchaseState, self).action(a, params)
