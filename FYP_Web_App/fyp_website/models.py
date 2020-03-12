from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class ExtractedRelation(models.Model):
    rel_id = models.AutoField(primary_key=True)
    ckpt = models.CharField(max_length=100)
    datetime_extracted = models.DateField(auto_now_add=True)
    sentence = models.CharField(max_length=10000)
    head = models.CharField(max_length=1000)
    tail = models.CharField(max_length=1000)
    pred_relation = models.CharField(max_length=1000)
    conf = models.IntegerField()
    sentiment = models.CharField(max_length=1000)
    source = models.CharField(max_length=1000)
    user = models.ForeignKey(User, related_name='extracted_relation', on_delete=models.SET_NULL, null=True)