from django.db import models
from rest_framework import serializers

from user.models import SysUser


# Role type constants
ROLE_SUPERADMIN = 'superadmin'  # 超级管理员
ROLE_ADMIN = 'admin'            # 管理员
ROLE_USER = 'user'              # 普通用户

class SysRole(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="角色名称")
    code = models.CharField(max_length=100, unique=True, verbose_name="角色权限字符串") 
    role_sort = models.IntegerField(default=1, verbose_name="显示顺序")
    status = models.IntegerField(default=0, verbose_name="角色状态（0正常 1停用）")
    create_time = models.DateTimeField(null=True, verbose_name="创建时间")
    update_time = models.DateTimeField(null=True, verbose_name="更新时间")
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name="备注")

    class Meta:
        db_table = "sys_role"
        verbose_name = "系统角色"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SysRoleSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    update_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)
    
    class Meta:
        model = SysRole
        fields = '__all__'


class SysUserRole(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey(SysRole, on_delete=models.CASCADE, verbose_name="角色")
    user = models.ForeignKey(SysUser, on_delete=models.CASCADE, verbose_name="用户", related_name='user_roles')

    class Meta:
        db_table = "sys_user_role"
        verbose_name = "用户角色关联"
        verbose_name_plural = verbose_name
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class SysUserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUserRole
        fields = '__all__'
