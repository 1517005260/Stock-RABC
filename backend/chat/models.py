from django.db import models
from user.models import SysUser
from django.utils import timezone
import datetime

class ChatMessage(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(SysUser, on_delete=models.CASCADE, verbose_name="用户")
    content = models.TextField(verbose_name="消息内容")
    response = models.TextField(verbose_name="GPT回复", null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")
    tokens_used = models.IntegerField(default=0, verbose_name="使用的tokens数量")
    model = models.CharField(max_length=50, default="gpt-4o", verbose_name="使用的模型")
    is_hidden = models.BooleanField(default=False, verbose_name="是否隐藏")
    
    class Meta:
        db_table = "chat_message"
        verbose_name = "聊天记录"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        
class ChatUsage(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(SysUser, on_delete=models.CASCADE, verbose_name="用户")
    usage_date = models.DateField(verbose_name="使用日期")
    usage_count = models.IntegerField(default=0, verbose_name="使用次数")
    
    class Meta:
        db_table = "chat_usage"
        verbose_name = "聊天使用统计"
        verbose_name_plural = verbose_name
        unique_together = [['user', 'usage_date']]
        
    @classmethod
    def get_today_usage(cls, user_id):
        """获取用户今日使用次数"""
        today = timezone.now().date()
        usage, created = cls.objects.get_or_create(
            user_id=user_id,
            usage_date=today,
            defaults={'usage_count': 0}
        )
        return usage
    
    @classmethod
    def increment_usage(cls, user_id):
        """增加用户使用次数"""
        usage = cls.get_today_usage(user_id)
        usage.usage_count += 1
        usage.save()
        return usage