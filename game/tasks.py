from django.db import IntegrityError, transaction
from celery import task
from celery.utils.log import get_task_logger

import json

from game.models import Game, GameLog, GameState, GameInfo, Action, GameInfoDecoder
#, GameLog, GameInfo, HouseInfo, HouseTurnLog, HouseBiddingLog, GameInfoEncoder, GameInfoDecoder, Action

@task()
def process_action(game_id, lsn):
    logger = get_task_logger(__name__)
    action_queue = []

    with transaction.atomic():
        g = Game.objects.get(hashkey=game_id)
        logs = GameLog.objects.filter(game=g, lsn__gt=g.applied_lsn, lsn__lte=lsn, status=GameLog.ACCEPTED)
        info = json.loads(g.current_info, cls=GameInfoDecoder)
        for l in logs:
            try:
                logger.info('Applying ' + str(l))
                action_dict = l.get_log_as_dict()
                state = GameState.getInstance(info)
                user_id = l.player.user_id if l.player != None else None
                result = state.action(action_dict['action'], user_id=user_id, params=action_dict)

                info = state.info
                if 'random' in result.keys():
                    action_dict['random'] = result['random']
                if 'queue_action' in result.keys() :
                    action_queue.append(result['queue_action'])

                l.set_log(action_dict)
                l.status = GameLog.CONFIRMED
            except (GameState.NotSupportedAction, GameState.InvalidAction, Action.InvalidParameter) as e:
                l.status = GameLog.FAILED
                logger.error(type(e).__name__ + ": " + e.message)
            g.applied_lsn = l.lsn
            l.save()
        g.set_current_info(info)

        for aq in action_queue:
            g.last_lsn += 1
            a = GameLog(
                    game=g,
                    player=None,
                    lsn=g.last_lsn,
                )
            a.set_log(log_dict=aq)
            a.save()
        g.save()

    if action_queue:
        process_action.delay(g.hashkey, g.last_lsn)

    return g.applied_lsn
