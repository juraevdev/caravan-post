from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class User(BaseModel):
    telegram_id = models.PositiveBigIntegerField(unique=True)
    full_name = models.CharField(max_length=255)
    username = models.CharField(max_length=128, null=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = "telegram_users"


class BotAdmin(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user.username)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            pass
        super(BotAdmin, self).save(*args, **kwargs)
        
    class Meta:
        db_table = "bot_admins"


class AdCounter(BaseModel):
    """Model to track ad IDs for each channel prefix"""
    channel_prefix = models.CharField(max_length=2, unique=True)  # TJ, KZ, etc.
    last_id = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.channel_prefix}: {self.last_id}"
    
    class Meta:
        db_table = "ad_counters"


class Advertisement(BaseModel):
    """Model to store advertisement data"""
    ad_id = models.CharField(max_length=12, unique=True)  # TJ00000001, KZ00000001
    channel_username = models.CharField(max_length=128)
    user_telegram_id = models.PositiveBigIntegerField()
    user_full_name = models.CharField(max_length=255)
    user_username = models.CharField(max_length=128, null=True)
    message_text = models.TextField()
    original_message_id = models.PositiveIntegerField(null=True, blank=True)  # Original user message ID for forwarding
    message_id = models.PositiveIntegerField(null=True, blank=True)  # Posted message ID in channel
    is_posted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.ad_id} - @{self.channel_username}"
    
    class Meta:
        db_table = "advertisements"