from celery import task

@task()
def process_action(game_id, lsn):
    return None
