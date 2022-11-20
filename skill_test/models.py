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


class Users(models.Model):
    u_id = models.AutoField(primary_key=True)
    name = models.TextField()
    email = models.TextField()
    phone = models.TextField()
    degree = models.TextField()
    year = models.TextField()
    dob = models.DateField()
    allowed_test = models.TextField()
    username = models.TextField()
    password = models.TextField()
    is_active = models.BooleanField()
    def __str__(self):
        return str(self.u_id)


class Batches(models.Model):
    b_id = models.TextField()
    u_ids = models.TextField()
    is_open = models.BooleanField()
    def __str__(self):
        return str(self.b_id)



class Results(models.Model):
    t_id = models.TextField()
    q_id = models.IntegerField()
    obtained_marks = models.FloatField()
    total_marks = models.FloatField()
    email = models.CharField(max_length=122)
    solution = models.TextField()
    t_cases = models.IntegerField()
    p_cases = models.IntegerField()
    def __str__(self):
        return self.email+"_"+str(self.t_id)+"_"+str(self.q_id)