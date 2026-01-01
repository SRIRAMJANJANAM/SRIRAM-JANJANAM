from django.db import models

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    msg = models.TextField(max_length=500)
    phone = models.CharField(max_length=15, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.email}"
    
    class Meta:
        ordering = ['-submitted_at']

class ChatMessage(models.Model):
    user_name = models.CharField(max_length=100, blank=True, null=True)
    user_email = models.EmailField(blank=True, null=True)
    user_phone = models.CharField(max_length=15, blank=True, null=True)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user_name or 'Anonymous'} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']

class Experience(models.Model):
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    currently_working = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.role} at {self.company}"
    
    class Meta:
        ordering = ['-start_date']