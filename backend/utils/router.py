# -*- coding: utf-8 -*-
from django.conf import settings

DATABASE_MAPPING = settings.DATABASE_APPS_MAPPING


class DatabaseAppsRouter(object):
    """
    一个路由器，用于控制不同数据库的模型上的所有数据库操作。如果未在设置中设置应用程序。
    DATABASE_APPS_MAPPING，路由器将回退到 'default' 数据库。设置示例：
    DATABASE_APPS_MAPPING = {'app1'： 'db1'， 'app2'： 'db2'}
    """

    def db_for_read(self, model, **hints):
        """将所有读取操作指向特定数据库。"""
        if model._meta.app_label in DATABASE_MAPPING:
            return DATABASE_MAPPING[model._meta.app_label]
        return None

    def db_for_write(self, model, **hints):
        """将所有写入操作指向特定数据库。"""
        if model._meta.app_label in DATABASE_MAPPING:
            return DATABASE_MAPPING[model._meta.app_label]
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """允许使用同一数据库的应用程序之间的任何关系。"""
        db_obj1 = DATABASE_MAPPING.get(obj1._meta.app_label)
        db_obj2 = DATABASE_MAPPING.get(obj2._meta.app_label)
        if db_obj1 and db_obj2:
            if db_obj1 == db_obj2:
                return True
            else:
                return False
        return None

    def allow_syncdb(self, db, model):
        """确保应用程序仅显示在相关数据库中。"""
        if db in DATABASE_MAPPING.values():
            return DATABASE_MAPPING.get(model._meta.app_label) == db
        elif model._meta.app_label in DATABASE_MAPPING:
            return False
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        """确保身份验证应用程序仅显示在“auth_db”数据库中。"""
        if db in DATABASE_MAPPING.values():
            return DATABASE_MAPPING.get(app_label) == db
        elif app_label in DATABASE_MAPPING:
            return False
        return None
