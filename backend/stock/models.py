# -*- coding: utf-8 -*-

from django.db import models
from rest_framework import serializers
from decimal import Decimal


class StockBasic(models.Model):
    """股票基本信息表 (基于Tushare stock_basic接口)"""
    ts_code = models.CharField(max_length=12, primary_key=True, verbose_name='TS股票代码')
    symbol = models.CharField(max_length=6, verbose_name='股票代码')
    name = models.CharField(max_length=20, verbose_name='股票名称')
    area = models.CharField(max_length=10, null=True, blank=True, verbose_name='地域')
    industry = models.CharField(max_length=20, null=True, blank=True, verbose_name='所属行业')
    fullname = models.CharField(max_length=100, null=True, blank=True, verbose_name='股票全称')
    enname = models.CharField(max_length=100, null=True, blank=True, verbose_name='英文全称')
    cnspell = models.CharField(max_length=20, null=True, blank=True, verbose_name='拼音缩写')
    market = models.CharField(max_length=10, null=True, blank=True, verbose_name='市场类型')
    exchange = models.CharField(max_length=10, null=True, blank=True, verbose_name='交易所代码')
    curr_type = models.CharField(max_length=10, null=True, blank=True, verbose_name='交易货币')
    list_status = models.CharField(max_length=1, null=True, blank=True, verbose_name='上市状态')
    list_date = models.DateField(null=True, blank=True, verbose_name='上市日期')
    delist_date = models.DateField(null=True, blank=True, verbose_name='退市日期')
    is_hs = models.CharField(max_length=1, null=True, blank=True, verbose_name='是否沪深港通')
    act_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='实控人名称')
    act_ent_type = models.CharField(max_length=20, null=True, blank=True, verbose_name='实控人企业性质')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'stock_basic'
        verbose_name = '股票基本信息'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['industry']),
            models.Index(fields=['market']),
            models.Index(fields=['list_status']),
        ]

    def __str__(self):
        return f"{self.ts_code} - {self.name}"


class StockDaily(models.Model):
    """股票日线行情 (基于Tushare daily接口)"""
    ts_code = models.CharField(max_length=12, db_index=True, verbose_name='TS股票代码')
    trade_date = models.DateField(db_index=True, verbose_name='交易日期')
    open = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='开盘价')
    high = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='最高价')
    low = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='最低价')
    close = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='收盘价')
    pre_close = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='昨收价')
    change = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='涨跌额')
    pct_chg = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='涨跌幅')
    vol = models.BigIntegerField(null=True, verbose_name='成交量(手)')
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, verbose_name='成交额(千元)')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'stock_daily'
        verbose_name = '股票日线行情'
        verbose_name_plural = verbose_name
        unique_together = ('ts_code', 'trade_date')
        indexes = [
            models.Index(fields=['ts_code', 'trade_date']),
            models.Index(fields=['trade_date']),
        ]
        ordering = ['-trade_date']

    def __str__(self):
        return f"{self.ts_code} - {self.trade_date}"


class StockCompany(models.Model):
    """上市公司基本信息 (基于Tushare stock_company接口)"""
    ts_code = models.CharField(max_length=12, primary_key=True, verbose_name='TS股票代码')
    exchange = models.CharField(max_length=10, null=True, blank=True, verbose_name='交易所代码')
    chairman = models.CharField(max_length=100, null=True, blank=True, verbose_name='法人代表')
    manager = models.CharField(max_length=100, null=True, blank=True, verbose_name='总经理')
    secretary = models.CharField(max_length=100, null=True, blank=True, verbose_name='董秘')
    reg_capital = models.DecimalField(max_digits=15, decimal_places=2, null=True, verbose_name='注册资本')
    setup_date = models.DateField(null=True, blank=True, verbose_name='注册日期')
    province = models.CharField(max_length=20, null=True, blank=True, verbose_name='所在省份')
    city = models.CharField(max_length=20, null=True, blank=True, verbose_name='所在城市')
    introduction = models.TextField(null=True, blank=True, verbose_name='公司介绍')
    website = models.URLField(null=True, blank=True, verbose_name='公司主页')
    email = models.EmailField(null=True, blank=True, verbose_name='电子邮件')
    office = models.CharField(max_length=200, null=True, blank=True, verbose_name='办公地址')
    employees = models.IntegerField(null=True, blank=True, verbose_name='员工人数')
    main_business = models.TextField(null=True, blank=True, verbose_name='主要业务及产品')
    business_scope = models.TextField(null=True, blank=True, verbose_name='经营范围')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'stock_company'
        verbose_name = '上市公司基本信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.ts_code} - 公司信息"


class TradeCal(models.Model):
    """交易日历 (基于Tushare trade_cal接口)"""
    exchange = models.CharField(max_length=10, verbose_name='交易所')
    cal_date = models.DateField(verbose_name='日历日期')
    is_open = models.BooleanField(verbose_name='是否交易')
    pretrade_date = models.DateField(null=True, blank=True, verbose_name='上一交易日')

    class Meta:
        db_table = 'trade_cal'
        verbose_name = '交易日历'
        verbose_name_plural = verbose_name
        unique_together = ('exchange', 'cal_date')
        indexes = [
            models.Index(fields=['exchange', 'cal_date']),
            models.Index(fields=['cal_date']),
        ]
        ordering = ['-cal_date']

    def __str__(self):
        return f"{self.exchange} - {self.cal_date}"


class IndexDaily(models.Model):
    """指数日线行情 (基于Tushare index_daily接口)"""
    ts_code = models.CharField(max_length=12, db_index=True, verbose_name='TS指数代码')
    trade_date = models.DateField(db_index=True, verbose_name='交易日期')
    close = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='收盘点位')
    open = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='开盘点位')
    high = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='最高点位')
    low = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='最低点位')
    pre_close = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='昨日收盘点')
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='涨跌点')
    pct_chg = models.DecimalField(max_digits=10, decimal_places=3, null=True, verbose_name='涨跌幅')
    vol = models.BigIntegerField(null=True, verbose_name='成交量(手)')
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, verbose_name='成交额(千元)')

    class Meta:
        db_table = 'index_daily'
        verbose_name = '指数日线行情'
        verbose_name_plural = verbose_name
        unique_together = ('ts_code', 'trade_date')
        indexes = [
            models.Index(fields=['ts_code', 'trade_date']),
        ]
        ordering = ['-trade_date']

    def __str__(self):
        return f"{self.ts_code} - {self.trade_date}"


# Serializers
class StockBasicSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    list_date = serializers.DateField(format="%Y-%m-%d", required=False)
    
    class Meta:
        model = StockBasic
        fields = '__all__'


class StockDailySerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    trade_date = serializers.DateField(format="%Y-%m-%d", required=False)
    
    class Meta:
        model = StockDaily
        fields = '__all__'


class StockCompanySerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    setup_date = serializers.DateField(format="%Y-%m-%d", required=False)
    
    class Meta:
        model = StockCompany
        fields = '__all__'


class TradeCalSerializer(serializers.ModelSerializer):
    cal_date = serializers.DateField(format="%Y-%m-%d", required=False)
    pretrade_date = serializers.DateField(format="%Y-%m-%d", required=False)
    
    class Meta:
        model = TradeCal
        fields = '__all__'


class IndexDailySerializer(serializers.ModelSerializer):
    trade_date = serializers.DateField(format="%Y-%m-%d", required=False)
    
    class Meta:
        model = IndexDaily
        fields = '__all__'
