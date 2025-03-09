from django.db import models


class Speaker(models.Model):
    name = models.CharField(max_length=100, unique=True)
    reference_text = models.TextField(blank=True)
    reference_audio = models.FileField(upload_to='speakers/')

    def __str__(self):
        return self.name
