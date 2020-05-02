from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Source(models.Model):
    """
        Models the particular source from which relations are extracted.
    """
    source_id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=1000)
    datetime_extracted = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='extracted_relation', on_delete=models.SET_NULL, null=True)
    
class ExtractedRelation(models.Model):
    """
        Models an extracted relation.
    """
    rel_id = models.AutoField(primary_key=True)
    ckpt = models.CharField(max_length=100)
    sentence = models.CharField(max_length=10000)
    head = models.CharField(max_length=1000)
    tail = models.CharField(max_length=1000)
    pred_relation = models.CharField(max_length=1000)
    conf = models.IntegerField()
    sentiment = models.CharField(max_length=1000)
    source = models.ForeignKey(Source, related_name='relation_source', on_delete=models.SET_NULL, null=True)