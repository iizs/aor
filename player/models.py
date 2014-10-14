from django.db import models
from django.utils import timezone

class Player(models.Model):
    IIZS_NET    = 'i'
    KAKAO_ID    = 'k'
    GOOGLE_ID   = 'g'
    AUTH_PROVIDER = (
        (IIZS_NET, 'iizs.net'), 
        (GOOGLE_ID, 'Google ID'), 
        (KAKAO_ID, 'KAKAO ID'), 
    )
    user_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, null=True, blank=True)
    auth_provider = models.CharField(max_length=1, choices=AUTH_PROVIDER, default=IIZS_NET)

    def __unicode__(self):
        return self.user_id

    class Meta:
        unique_together = (
            ("auth_provider", "user_id"),
        )


class AccessToken(models.Model):
    player = models.OneToOneField(Player)
    token = models.CharField(max_length=255, db_index=True)
    expires = models.DateTimeField()

    def is_expired(self):
        return timezone.now() >= self.expires

    def is_valid(self):
        return not self.is_expired() 

    def __unicode__(self):
        return self.token

    class Invalid(Exception):
        def __init__(self, value):
            self.value = value
        def __unicode__(self):
            return repr(self.value)

    class Expired(Exception):
        def __init__(self, value):
            self.value = value
        def __unicode__(self):
            return repr(self.value)

