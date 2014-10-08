from django.db import models

class Player(models.Model):
    user_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return self.user_id
