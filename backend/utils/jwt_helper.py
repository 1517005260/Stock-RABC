# -*- coding: utf-8 -*-
"""
JWT辅助工具
"""
import jwt
from django.conf import settings
from rest_framework_jwt.settings import api_settings


def decode_jwt_token(token):
    """解码JWT token"""
    try:
        jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
        payload = jwt_decode_handler(token)
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def encode_jwt_token(payload):
    """编码JWT token"""
    try:
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        return jwt_encode_handler(payload)
    except Exception:
        return None