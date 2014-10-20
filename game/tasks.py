from django.db import IntegrityError, transaction
from celery import task
from celery.utils.log import get_task_logger

from game.models import Game, GameLog, GameState, GameInfo
#, GameLog, GameInfo, HouseInfo, HouseTurnLog, HouseBiddingLog, GameInfoEncoder, GameInfoDecoder, Action

@task()
def process_action(game_id, lsn):
    logger = get_task_logger(__name__)

    with transaction.atomic():
        g = Game.objects.get(hashkey=game_id)
        logs = GameLog.objects.filter(game=g, lsn__gt=g.applied_lsn, lsn__lte=lsn, status=GameLog.ACCEPTED)
        info = GameInfo(g)
        for l in logs:
            try:
                logger.info('Applying ' + str(l))
                action_dict = l.get_log_as_dict()
                state = GameState.getInstance(info)
                rand_dict = state.action(action_dict['action'], params=action_dict)
                info = state.info
                action_dict['random'] = rand_dict
                l.set_log(action_dict)
                l.status = GameLog.CONFIRMED
            except GameState.NotSupportedAction as e:
                l.status = GameLog.FAILED
                logger.error('GameState.NotSupportedAction: ' + str(l))
            g.applied_lsn = l.lsn
            l.save()
        g.set_current_info(info)
        g.save()
    return g.applied_lsn
