import json
import asyncio
import datetime
import os
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.db import transaction
from asgiref.sync import sync_to_async
from rest_framework.views import APIView
from django.conf import settings
from openai import AsyncOpenAI
from dotenv import load_dotenv

from .models import ChatMessage, ChatUsage
from role.models import SysUserRole, SysRole, ROLE_SUPERADMIN, ROLE_ADMIN

# 尝试加载环境变量，如果失败就使用默认值
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: 无法加载.env文件: {e}")

# 创建OpenAI客户端，使用环境变量或默认值
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 2000))
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
CHAT_DAILY_LIMIT = int(os.getenv('CHAT_DAILY_LIMIT', 5))

# 如果API密钥不可用，使用模拟模式
USE_MOCK = OPENAI_API_KEY == 'your_openai_api_key_here'

# 创建OpenAI客户端（如果有API密钥）
client = None
if not USE_MOCK:
    try:
        # 清除代理环境变量
        for env_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
            if env_var in os.environ:
                del os.environ[env_var]
        
        # 创建AsyncOpenAI客户端，不使用代理参数
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
    except Exception as e:
        print(f"Warning: 无法初始化OpenAI客户端: {e}")
        USE_MOCK = True

async def get_gpt_response(message):
    """与OpenAI API进行流式通信或提供模拟响应"""
    try:
        if USE_MOCK:
            # 模拟响应，用于演示或测试
            mock_response = f"这是一个模拟的GPT回复。\n\n您的消息是: {message}\n\n在实际部署中，您需要在.env文件中配置OPENAI_API_KEY。"
            for word in mock_response.split():
                yield f"data: {word} "
                await asyncio.sleep(0.1)  # 模拟网络延迟
            yield f"data: [DONE]\n\n"
        else:
            # 实际调用OpenAI API
            try:
                response = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role": "user", "content": message}],
                    temperature=OPENAI_TEMPERATURE,
                    max_tokens=OPENAI_MAX_TOKENS,
                    stream=True,
                )
                
                async for chunk in response:
                    try:
                        # 增强错误检查，确保所有属性都存在
                        if (chunk and 
                            hasattr(chunk, 'choices') and 
                            chunk.choices and 
                            len(chunk.choices) > 0 and 
                            hasattr(chunk.choices[0], 'delta') and 
                            chunk.choices[0].delta and 
                            hasattr(chunk.choices[0].delta, 'content') and 
                            chunk.choices[0].delta.content):
                            content = chunk.choices[0].delta.content
                            yield f"data: {content}\n\n"
                    except (IndexError, AttributeError) as e:
                        print(f"处理API响应块时出错: {e}, chunk={chunk}")
                        continue
                
                yield f"data: [DONE]\n\n"
            except Exception as e:
                print(f"API调用错误: {e}")
                # 如果API调用失败，返回错误消息
                error_msg = f"调用API时发生错误: {str(e)}"
                yield f"data: {error_msg}\n\n"
                yield f"data: [DONE]\n\n"
            
    except Exception as e:
        print(f"处理响应时发生错误: {e}")
        yield f"data: 错误: {str(e)}\n\n"
        yield f"data: [DONE]\n\n"

class ChatView(APIView):
    def get(self, request):
        """获取用户聊天历史"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return JsonResponse({'code': 401, 'message': '未授权'}, status=401)
        
        try:
            # 获取最近的30条聊天记录，排除已隐藏的记录
            chat_history = ChatMessage.objects.filter(
                user_id=user_id, 
                is_completed=True,
                is_hidden=False  # 只获取未隐藏的记录
            ).order_by('-created_time')[:30]
            
            # 检查用户的使用限制
            # 获取用户角色
            user_roles = list(SysRole.objects.raw(
                "SELECT r.id, r.code, r.name FROM sys_role r "
                "JOIN sys_user_role ur ON r.id = ur.role_id "
                "WHERE ur.user_id=%s",
                [user_id]
            ))
            
            # 检查是否为管理员或超级管理员
            is_admin = any(role.code == ROLE_ADMIN or role.code == ROLE_SUPERADMIN for role in user_roles)
            
            # 获取今日使用次数
            today_usage = ChatUsage.get_today_usage(user_id)
            today_count = today_usage.usage_count
            
            # 普通用户每日限制
            daily_limit = CHAT_DAILY_LIMIT
            can_chat = is_admin or today_count < daily_limit
            
            result = {
                'code': 200,
                'chat_history': [
                    {
                        'id': chat.id,
                        'content': chat.content,
                        'response': chat.response,
                        'created_time': chat.created_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'tokens_used': chat.tokens_used,
                        'model': chat.model
                    } for chat in chat_history
                ],
                'usage': {
                    'is_admin': is_admin,
                    'today_count': today_count,
                    'daily_limit': daily_limit if not is_admin else None,
                    'can_chat': can_chat
                }
            }
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'code': 500, 'message': f'获取聊天记录失败: {str(e)}'}, status=500)
    
    def post(self, request):
        """创建新的聊天消息"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return JsonResponse({'code': 401, 'message': '未授权'}, status=401)
        
        try:
            data = json.loads(request.body.decode("utf-8"))
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({'code': 400, 'message': '消息内容不能为空'}, status=400)
            
            # 检查用户角色和使用限制
            # 获取用户角色
            user_roles = list(SysRole.objects.raw(
                "SELECT r.id, r.code, r.name FROM sys_role r "
                "JOIN sys_user_role ur ON r.id = ur.role_id "
                "WHERE ur.user_id=%s",
                [user_id]
            ))
            
            # 检查是否为管理员或超级管理员
            is_admin = any(role.code == ROLE_ADMIN or role.code == ROLE_SUPERADMIN for role in user_roles)
            
            # 获取今日使用记录
            today_usage = ChatUsage.get_today_usage(user_id)
            
            # 普通用户每日限制
            if not is_admin and today_usage.usage_count >= CHAT_DAILY_LIMIT:
                return JsonResponse({
                    'code': 403, 
                    'message': f'您今日的对话次数已达上限({CHAT_DAILY_LIMIT}次)'
                }, status=403)
            
            # 创建聊天消息记录
            with transaction.atomic():
                chat = ChatMessage.objects.create(
                    user_id=user_id,
                    content=message,
                    is_completed=False,
                    model=OPENAI_MODEL
                )
                
                # 更新使用次数
                ChatUsage.increment_usage(user_id)
            
            return JsonResponse({
                'code': 200, 
                'message': '消息已发送',
                'chat_id': chat.id,
                'usage': {
                    'is_admin': is_admin,
                    'today_count': today_usage.usage_count + 1,
                    'daily_limit': CHAT_DAILY_LIMIT if not is_admin else None
                }
            })
            
        except Exception as e:
            return JsonResponse({'code': 500, 'message': f'发送消息失败: {str(e)}'}, status=500)

    def put(self, request):
        """隐藏/清除用户聊天历史"""
        user_id = getattr(request, 'user_id', None)
        if not user_id:
            return JsonResponse({'code': 401, 'message': '未授权'}, status=401)
        
        try:
            # 解析请求数据
            data = json.loads(request.body.decode("utf-8"))
            action = data.get('action', '')  # 'hide_all', 'hide_single', 'unhide_all'
            message_id = data.get('message_id', None)
            
            if action == 'hide_all':
                # 隐藏用户的所有聊天记录
                with transaction.atomic():
                    affected_rows = ChatMessage.objects.filter(
                        user_id=user_id,
                        is_completed=True
                    ).update(is_hidden=True)
                    
                return JsonResponse({
                    'code': 200,
                    'message': f'成功隐藏{affected_rows}条聊天记录',
                    'affected_rows': affected_rows
                })
                
            elif action == 'hide_single' and message_id:
                # 隐藏单条聊天记录
                with transaction.atomic():
                    message = ChatMessage.objects.get(id=message_id, user_id=user_id)
                    message.is_hidden = True
                    message.save()
                    
                return JsonResponse({
                    'code': 200,
                    'message': f'成功隐藏ID为{message_id}的聊天记录'
                })
                
            elif action == 'unhide_all':
                # 取消隐藏所有记录
                with transaction.atomic():
                    affected_rows = ChatMessage.objects.filter(
                        user_id=user_id,
                        is_hidden=True
                    ).update(is_hidden=False)
                    
                return JsonResponse({
                    'code': 200,
                    'message': f'成功取消隐藏{affected_rows}条聊天记录',
                    'affected_rows': affected_rows
                })
                
            else:
                return JsonResponse({
                    'code': 400,
                    'message': '无效的操作或参数'
                }, status=400)
            
        except ChatMessage.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '聊天记录不存在'}, status=404)
        except Exception as e:
            return JsonResponse({'code': 500, 'message': f'操作失败: {str(e)}'}, status=500)

async def chat_stream(request, chat_id):
    """流式响应聊天消息"""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        yield "data: 未授权\n\n"
        return
    
    try:
        # 同步查询转为异步
        @sync_to_async
        def get_chat_message():
            try:
                return ChatMessage.objects.get(id=chat_id, user_id=user_id, is_completed=False)
            except ChatMessage.DoesNotExist:
                return None
        
        @sync_to_async
        def update_chat_message(chat, response, tokens=0):
            chat.response = response
            chat.is_completed = True
            chat.tokens_used = tokens
            chat.save()
        
        chat = await get_chat_message()
        if not chat:
            yield "data: 聊天消息不存在或已完成\n\n"
            return
        
        # 获取GPT响应
        full_response = ""
        try:
            async for chunk in get_gpt_response(chat.content):
                yield chunk
                # 确保数据格式正确并提取内容
                if isinstance(chunk, str) and "data: " in chunk and "[DONE]" not in chunk:
                    try:
                        content = chunk.replace("data: ", "").replace("\n\n", "")
                        full_response += content
                    except Exception as e:
                        print(f"处理响应内容时出错: {e}, chunk={chunk}")
                        continue
        except Exception as e:
            error_msg = f"获取响应时出错: {str(e)}"
            print(error_msg)
            yield f"data: {error_msg}\n\n"
            yield f"data: [DONE]\n\n"
            full_response = error_msg
        
        # 估算token数量 (简单估算，实际应从API响应获取)
        tokens = len(chat.content.split()) + len(full_response.split())
        
        # 更新数据库中的消息
        await update_chat_message(chat, full_response, tokens)
        
    except Exception as e:
        error_msg = f"流式响应错误: {str(e)}"
        print(error_msg)
        yield f"data: {error_msg}\n\n"
        yield f"data: [DONE]\n\n"

# 流式聊天响应视图
class ChatStreamView(View):
    def get(self, request, chat_id):
        print(f"开始处理聊天流响应: chat_id={chat_id}, user_id={getattr(request, 'user_id', 'None')}")
        
        # 确保流式响应的认证通过
        if not hasattr(request, 'user_id'):
            print(f"聊天流未授权: {request.path}")
            return StreamingHttpResponse(
                "data: 未授权，请确保已登录\n\n", 
                content_type='text/event-stream'
            )
        
        response = StreamingHttpResponse(
            chat_stream(request, chat_id),
            content_type='text/event-stream'
        )
        # 添加必要的SSE响应头
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # 防止Nginx缓冲
        response['Access-Control-Allow-Origin'] = '*'  # 允许跨域
        return response