# -*- coding: utf-8 -*-

from django.db import models
from rest_framework import serializers


class SysUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, verbose_name="用户名")
    password = models.CharField(max_length=100, verbose_name="密码")
    avatar = models.CharField(max_length=255, null=True, verbose_name="用户头像")
    email = models.CharField(max_length=100, null=True, verbose_name="用户邮箱")
    phonenumber = models.CharField(max_length=11, null=True, verbose_name="手机号码")
    login_date = models.DateTimeField(null=True, verbose_name="最后登录时间")
    status = models.IntegerField(null=True, verbose_name="账号状态（0正常 1停用）")
    create_time = models.DateTimeField(null=True, verbose_name="创建时间")
    update_time = models.DateTimeField(null=True, verbose_name="更新时间")
    remark = models.CharField(max_length=500, null=True, verbose_name="备注")

    class Meta:
        db_table = "sys_user"


class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = '__all__'
