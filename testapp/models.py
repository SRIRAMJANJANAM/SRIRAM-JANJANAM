from django.db import models

# Create your models here.
class Contact(models.Model):
    name=models.CharField(max_length=40)
    email=models.EmailField()
    msg=models.CharField(max_length=250)

class ChatMessage(models.Model):
    user_message = models.CharField(max_length=250)
    bot_response = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"User: {self.user_message} - Bot: {self.bot_response}"