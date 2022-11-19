from django.db import models

# Create your models here.
class Questions(models.Model):
    t_id = models.TextField()
    q_id = models.IntegerField()
    statement = models.TextField()
    groundtruths = models.TextField()
    solution = models.TextField()
    score = models.FloatField()
    def __str__(self):
        return str(self.t_id)+"_"+str(self.q_id)
    

class Tests(models.Model):
    t_id = models.TextField()
    is_open = models.BooleanField()
    def __str__(self):
        return str(self.t_id)
    