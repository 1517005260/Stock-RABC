# -*- coding: utf-8 -*-

from django.db import models
from rest_framework import serializers
from decimal import Decimal
from user.models import SysUser


class UserStockAccount(models.Model):
    """用户股票账户表"""
    user = models.OneToOneField(SysUser, on_delete=models.CASCADE, verbose_name='用户')
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00, verbose_name='可用资金')
    frozen_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name='冻结资金')
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00, verbose_name='总资产')
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name='总盈亏')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user_stock_account'
        verbose_name = '用户股票账户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} - 股票账户"


class UserPosition(models.Model):
    """用户持仓表"""
    user = models.ForeignKey(SysUser, on_delete=models.CASCADE, verbose_name='用户')
    ts_code = models.CharField(max_length=12, verbose_name='TS股票代码')
    stock_name = models.CharField(max_length=20, verbose_name='股票名称')
    position_shares = models.IntegerField(default=0, verbose_name='持仓数量')
    available_shares = models.IntegerField(default=0, verbose_name='可用数量')
    cost_price = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='成本价')
    current_price = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name='当前价')
    profit_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='盈亏金额')
    profit_loss_ratio = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name='盈亏比例')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user_position'
        verbose_name = '用户持仓'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'ts_code')
        indexes = [
            models.Index(fields=['user', 'ts_code']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.ts_code}"


class TradeRecord(models.Model):
    """交易记录表"""
    TRADE_TYPE_CHOICES = [
        ('BUY', '买入'),
        ('SELL', '卖出'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '待成交'),
        ('COMPLETED', '已成交'),
        ('CANCELLED', '已撤销'),
    ]

    user = models.ForeignKey(SysUser, on_delete=models.CASCADE, verbose_name='用户')
    ts_code = models.CharField(max_length=12, verbose_name='TS股票代码')
    stock_name = models.CharField(max_length=20, verbose_name='股票名称')
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPE_CHOICES, verbose_name='交易类型')
    trade_price = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='交易价格')
    trade_shares = models.IntegerField(verbose_name='交易数量')
    trade_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='交易金额')
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, verbose_name='手续费')
    trade_time = models.DateTimeField(auto_now_add=True, verbose_name='交易时间')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='COMPLETED', verbose_name='状态')
    remark = models.CharField(max_length=200, null=True, blank=True, verbose_name='备注')

    class Meta:
        db_table = 'trade_record'
        verbose_name = '交易记录'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['user', 'trade_time']),
            models.Index(fields=['ts_code', 'trade_time']),
            models.Index(fields=['trade_time']),
        ]
        ordering = ['-trade_time']

    def __str__(self):
        return f"{self.user.username} - {self.trade_type} - {self.ts_code}"


class UserWatchList(models.Model):
    """自选股表"""
    user = models.ForeignKey(SysUser, on_delete=models.CASCADE, verbose_name='用户')
    ts_code = models.CharField(max_length=12, verbose_name='TS股票代码')
    stock_name = models.CharField(max_length=20, verbose_name='股票名称')
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        db_table = 'user_watch_list'
        verbose_name = '自选股'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'ts_code')
        indexes = [
            models.Index(fields=['user']),
        ]
        ordering = ['-add_time']

    def __str__(self):
        return f"{self.user.username} - {self.ts_code}"


class MarketNews(models.Model):
    """市场新闻表"""
    title = models.CharField(max_length=200, verbose_name='新闻标题')
    content = models.TextField(verbose_name='新闻内容')
    source = models.CharField(max_length=50, null=True, blank=True, verbose_name='新闻来源')
    publish_time = models.DateTimeField(verbose_name='发布时间')
    read_count = models.IntegerField(default=0, verbose_name='阅读次数')
    category = models.CharField(max_length=20, null=True, blank=True, verbose_name='新闻分类')
    related_stocks = models.JSONField(null=True, blank=True, verbose_name='相关股票代码')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'market_news'
        verbose_name = '市场新闻'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['publish_time']),
            models.Index(fields=['category']),
        ]
        ordering = ['-publish_time']

    def __str__(self):
        return self.title


# Serializers
class UserStockAccountSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    
    class Meta:
        model = UserStockAccount
        fields = ['user', 'username', 'account_balance', 'frozen_balance', 
                 'total_assets', 'total_profit', 'create_time', 'update_time']


class UserPositionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    
    class Meta:
        model = UserPosition
        fields = '__all__'


class TradeRecordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    trade_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    trade_type_display = serializers.CharField(source='get_trade_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TradeRecord
        fields = '__all__'


class UserWatchListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    add_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    
    class Meta:
        model = UserWatchList
        fields = '__all__'


class MarketNewsSerializer(serializers.ModelSerializer):
    publish_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    
    class Meta:
        model = MarketNews
        fields = '__all__'
