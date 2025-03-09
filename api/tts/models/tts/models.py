from django.db import models


class UsageLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    prompt_text = models.TextField()
    generated_text = models.TextField(blank=True)
    reference_text = models.TextField(blank=True)
    reference_audio = models.FileField(upload_to='usage/reference/', blank=True, null=True)
    generated_audio = models.FileField(upload_to='usage/generated/', blank=True, null=True)

    def __str__(self):
        return f"UsageLog {self.id} at {self.timestamp}"
