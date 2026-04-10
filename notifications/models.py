from django.db import models
from django.contrib.auth.models import User

class Notice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notices')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'Notice to {self.user.username}'
