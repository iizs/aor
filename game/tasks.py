from django.db import IntegrityError, transaction
from celery import task
from celery.utils.log import get_task_logger

from game.models import Game, GameLog, GameState, GameInfo
#, GameLog, GameInfo, HouseInfo, HouseTurnLog, HouseBiddingLog, GameInfoEncoder, GameInfoDecoder, Action

@task()
def process_action(game_id, lsn):
    logger = get_task_logger(__name__)

    with transaction.atomic():
        logger.info('task')
        g = Game.objects.get(hashkey=game_id)
        logs = GameLog.objects.filter(game=g, lsn__gt=g.applied_lsn, lsn__lte=lsn, status=GameLog.ACCEPTED)
        info = GameInfo(g)
        for l in logs:
            try:
                action_dict = l.get_log_as_dict()
                state = GameState.getInstance(info)
                state.action(action_dict['action'], params=action_dict)
                info = state.info
                l.status = GameLog.CONFIRMED
            except GameState.NotSupportedAction as e:
                l.status = GameLog.FAILED
                logger.error('GameState.NotSupportedAction')
            g.applied_lsn = l.lsn
            l.save()
        g.set_current_info(info)
        g.save()
    return g.applied_lsn
