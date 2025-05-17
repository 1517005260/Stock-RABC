import json
from datetime import datetime

from django.core.paginator import Paginator
from django.http import JsonResponse
# from django.views import View
from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework_jwt.settings import api_settings

from app import settings
# from menu.models import SysMenu, SysMenuSerializer
from role.models import SysRole, SysUserRole, ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_USER
from user.models import SysUser, SysUserSerializer


# @method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):

    def post(self, request):
        username = request.GET.get("username")
        password = request.GET.get("password")
        try:
            user = SysUser.objects.get(username=username, password=password)
            
            # 检查用户状态，只允许正常状态（status=0）的用户登录
            if user.status == 0:  # status=0 表示禁用，status=1 表示正常
                return JsonResponse({'code': 403, 'info': '账号已被禁用，请联系管理员！'})
                
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            # 将用户对象传递进去，获取到该对象的属性值
            payload = jwt_payload_handler(user)
            # 将属性值编码成jwt格式的字符串
            token = jwt_encode_handler(payload)

            roleList = SysRole.objects.raw("select id, name, code from sys_role where id in (select role_id from "
                                           "sys_user_role where user_id=" + str(user.id) + ")")

            print(roleList)

            # 获取当前用户所有的角色，逗号隔开
            roles = ",".join([role.name for role in roleList])
            role_codes = [role.code for role in roleList]
            
            # 将用户数据序列化
            user_data = SysUserSerializer(user).data
            # 添加角色信息到用户数据
            user_data['roles'] = roles
            
            # 添加权限信息
            permissions = []
            
            # 确定用户角色类型和对应的权限
            is_superadmin = ROLE_SUPERADMIN in role_codes or '超级管理员' in [role.name for role in roleList]
            is_admin = ROLE_ADMIN in role_codes or '管理员' in [role.name for role in roleList]
            
            # 1. 超级管理员拥有所有权限
            if is_superadmin:
                permissions = [
                    # 用户管理权限
                    'system:user:list', 'system:user:edit', 'system:user:add', 'system:user:remove', 'system:user:reset',
                    # 角色管理权限
                    'system:role:list', 'system:role:edit', 'system:role:add', 'system:role:remove',
                    # 个人管理权限
                    'system:user:profile',
                    # 聊天权限
                    'system:chat:use',
                ]
            # 2. 管理员有角色管理权限
            elif is_admin:
                permissions = [
                    # 用户管理权限（不包括删除用户）
                    'system:user:list', 'system:user:edit', 'system:user:add', 'system:user:reset',
                    # 角色查看权限（只读）
                    'system:role:list',
                    # 个人管理权限
                    'system:user:profile',
                    # 聊天权限
                    'system:chat:use',
                ]
            # 3. 普通用户只有查看权限
            else:
                permissions = [
                    # 只读权限
                    'system:user:list', 'system:role:list',
                    # 个人管理权限
                    'system:user:profile',
                    # 聊天权限
                    'system:chat:use',
                ]

            return JsonResponse({
                'code': 200, 
                'info': '登录成功', 
                'token': token, 
                'user': user_data,
                'permissions': permissions
            })

        except Exception as e:
            print(e)
            return JsonResponse({'code': 500, 'info': '用户不存在或密码错误！'})


# @method_decorator(csrf_exempt, name='dispatch')
class TestView(APIView):

    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        print("token:", token)
        if token != None and token != '':
            userList_obj = SysUser.objects.all()
            print(userList_obj, type(userList_obj))
            userList_dict = userList_obj.values()  # 转存字典
            print(userList_dict, type(userList_dict))
            userList = list(userList_dict)  # 把外层的容器转存List
            print(userList, type(userList))
            return JsonResponse({'code': 200, 'info': '测试!', 'data': userList})
        else:
            return JsonResponse({'code': 401, 'info': '没有访问权限!'})


# @method_decorator(csrf_exempt, name='dispatch')
class JwtTestView(APIView):

    # @csrf_exempt
    def get(self, request):
        user = SysUser.objects.get(username='long', password='123456')
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        # 将用户对象传递进去，获取到该对象的属性值
        payload = jwt_payload_handler(user)
        # 将属性值编码成jwt格式的字符串
        token = jwt_encode_handler(payload)
        return JsonResponse({'code': 200, 'token': token})


class SaveView(APIView):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        # 获取当前登录用户信息
        user_id = getattr(request, 'user_id', None)
        
        # 检查是否是用户自己的操作
        is_self_operation = user_id and data.get('id') == user_id
        
        # 查询用户角色
        user_roles = SysRole.objects.raw(
            "SELECT id, code, name FROM sys_role WHERE id IN "
            "(SELECT role_id FROM sys_user_role WHERE user_id=%s)", 
            [user_id]
        )
        
        # 检查是否为超级管理员
        is_superadmin = False
        for role in user_roles:
            if role.code == ROLE_SUPERADMIN or role.name == '超级管理员':
                is_superadmin = True
                break
        
        # 权限检查
        if not is_self_operation and not is_superadmin:
            # 非超级管理员不能修改他人信息
            if data.get('id') != -1:
                return JsonResponse({'code': 403, 'message': '权限不足，只能修改自己的个人信息'}, status=403)
            # 非超级管理员不能添加用户
            else:
                return JsonResponse({'code': 403, 'message': '权限不足，只有超级管理员可以添加用户'}, status=403)
        
        if data['id'] == -1:  # 添加
            obj_sysUser = SysUser(username=data['username'], password=data['password'], email=data['email'],
                                  phonenumber=data['phonenumber'], status=data['status'], remark=data['remark'])
            obj_sysUser.create_time = datetime.now()
            obj_sysUser.avatar = 'default.jpg'
            obj_sysUser.password = '123456'

            obj_sysUser.save()
        else:  # 修改
            # 如果是自己修改信息，不允许修改状态和创建时间等敏感字段
            if is_self_operation:
                # 获取原始用户信息
                original_user = SysUser.objects.get(id=data['id'])
                
                # 保持原始数据不变的字段
                obj_sysUser = SysUser(
                    id=data['id'], 
                    username=data['username'], 
                    password=original_user.password,  # 保持密码不变
                    avatar=data.get('avatar', original_user.avatar),  # 使用新的头像或保持原头像
                    email=data['email'], 
                    phonenumber=data['phonenumber'],
                    login_date=original_user.login_date, 
                    status=original_user.status,  # 保持状态不变
                    create_time=original_user.create_time,
                    update_time=datetime.now(), 
                    remark=data.get('remark', original_user.remark)  # 使用新的备注或保持原备注
                )
            else:
                # 超级管理员可以修改所有字段
                obj_sysUser = SysUser(id=data['id'], username=data['username'], password=data['password'],
                                      avatar=data['avatar'], email=data['email'], phonenumber=data['phonenumber'],
                                      login_date=data['login_date'], status=data['status'], create_time=data['create_time'],
                                      update_time=datetime.now(), remark=data['remark'])
            
            obj_sysUser.save()
            
            # 如果是修改自己的信息，返回更新后的用户数据
            if is_self_operation:
                return JsonResponse({
                    'code': 200,
                    'message': '个人信息修改成功',
                    'user': SysUserSerializer(obj_sysUser).data
                })
            else:
                return JsonResponse({'code': 200, 'message': '用户信息修改成功'})


class ActionView(APIView):
    def get(self, request):
        """
        根据id获取用户信息
        :param request:
        :return:
        """
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        return JsonResponse({'code': 200, 'user': SysUserSerializer(user_object).data})

    def delete(self, request):
        """
        删除操作
        :param request:
        :return:
        """
        idList = json.loads(request.body.decode("utf-8"))
        SysUserRole.objects.filter(user_id__in=idList).delete()
        SysUser.objects.filter(id__in=idList).delete()
        return JsonResponse({'code': 200})


class CheckView(APIView):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        username = data['username']
        print("username=", username)
        if SysUser.objects.filter(username=username).exists():
            return JsonResponse({'code': 500})
        else:
            return JsonResponse({'code': 200})




class PwdView(APIView):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        oldPassword = data['oldPassword']
        newPassword = data['newPassword']
        obj_user = SysUser.objects.get(id=id)
        if obj_user.password == oldPassword:
            obj_user.password = newPassword
            obj_user.update_time = datetime.now()
            obj_user.save()
            return JsonResponse({'code': 200})
        else:
            return JsonResponse({'code': 500, 'errorInfo': '原密码错误！'})


class ImageView(APIView):

    def post(self, request):
        file = request.FILES.get('avatar')
        print("file:", file)
        if file:
            file_name = file.name
            suffixName = file_name[file_name.rfind("."):]
            new_file_name = datetime.now().strftime('%Y%m%d%H%M%S') + suffixName
            file_path = str(settings.MEDIA_ROOT) + "\\userAvatar\\" + new_file_name
            print("file_path:", file_path)
            try:
                with open(file_path, 'wb') as f:
                    for chunk in file.chunks():
                        f.write(chunk)
                return JsonResponse({'code': 200, 'title': new_file_name})
            except:
                return JsonResponse({'code': 500, 'errorInfo': '上传头像失败'})



class AvatarView(APIView):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        avatar = data['avatar']
        obj_user = SysUser.objects.get(id=id)
        obj_user.avatar = avatar
        obj_user.save()
        return JsonResponse({'code': 200})


class SearchView(APIView):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        pageNum = data['pageNum']  # 当前页
        pageSize = data['pageSize']  # 每页大小
        query = data['query']  # 查询参数
        print(pageSize, pageNum)
        userListPage = Paginator(SysUser.objects.filter(username__icontains=query), pageSize).page(pageNum)
        print(userListPage)
        obj_users = userListPage.object_list.values()  # 转成字典
        users = list(obj_users)  # 把外层的容器转成List
        for user in users:
            userId = user['id']
            roleList = SysRole.objects.raw("select id,name from sys_role where id in (select role_id from "
                                           "sys_user_role where user_id=" + str(userId) + ")")
            roleListDict = []
            for role in roleList:
                roleDict = {}
                roleDict['id'] = role.id
                roleDict['name'] = role.name
                roleListDict.append(roleDict)
            user['roleList'] = roleListDict
        total = SysUser.objects.filter(username__icontains=query).count()
        return JsonResponse({'code': 200, 'userList': users, 'total': total})


# 重置密码
class PasswordView(APIView):
    def get(self, request):
        id = request.GET.get("id")
        user_object = SysUser.objects.get(id=id)
        user_object.password = "123456"
        user_object.update_time = datetime.now()
        user_object.save()
        return JsonResponse({'code': 200})


# 用户状态修改
class StatusView(APIView):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        id = data['id']
        status = data['status']
        user_object = SysUser.objects.get(id=id)
        user_object.status = status
        user_object.save()
        return JsonResponse({'code': 200})


# 用户角色授权
class GrantRole(APIView):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        user_id = data['id']
        roleIdList = data['roleIds']
        print(user_id, roleIdList)
        SysUserRole.objects.filter(user_id=user_id).delete()  # 删除用户角色关联表中的指定用户数据
        for roleId in roleIdList:
            userRole = SysUserRole(user_id=user_id, role_id=roleId)
            userRole.save()
        return JsonResponse({'code': 200})


# 获取当前用户信息
class CurrentUserView(APIView):
    def get(self, request):
        try:
            # 从请求头获取token
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if not auth_header:
                return JsonResponse({'code': 401, 'msg': '未授权'})
            
            # 解析token获取用户信息
            token = auth_header.split(' ')[1] if len(auth_header.split(' ')) > 1 else auth_header
            jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
            payload = jwt_decode_handler(token)
            user_id = payload.get('user_id')
            
            # 获取用户信息
            user = SysUser.objects.get(id=user_id)
            user_data = SysUserSerializer(user).data
            
            # 获取用户角色
            roleList = SysRole.objects.raw("select id, name, code from sys_role where id in (select role_id from "
                                          "sys_user_role where user_id=" + str(user_id) + ")")
            
            # 获取当前用户所有的角色，逗号隔开
            roles = ",".join([role.name for role in roleList])
            role_codes = [role.code for role in roleList]
            user_data['roles'] = roles
            
            # 添加权限信息
            permissions = []
            
            # 确定用户角色类型和对应的权限
            is_superadmin = ROLE_SUPERADMIN in role_codes or '超级管理员' in [role.name for role in roleList]
            is_admin = ROLE_ADMIN in role_codes or '管理员' in [role.name for role in roleList]
            
            # 1. 超级管理员拥有所有权限
            if is_superadmin:
                permissions = [
                    # 用户管理权限
                    'system:user:list', 'system:user:edit', 'system:user:add', 'system:user:remove', 'system:user:reset',
                    # 角色管理权限
                    'system:role:list', 'system:role:edit', 'system:role:add', 'system:role:remove',
                    # 个人管理权限
                    'system:user:profile',
                    # 聊天权限
                    'system:chat:use',
                ]
            # 2. 管理员有角色管理权限
            elif is_admin:
                permissions = [
                    # 用户管理权限（不包括删除用户）
                    'system:user:list', 'system:user:edit', 'system:user:add', 'system:user:reset',
                    # 角色查看权限（只读）
                    'system:role:list',
                    # 个人管理权限
                    'system:user:profile',
                    # 聊天权限
                    'system:chat:use',
                ]
            # 3. 普通用户只有查看权限
            else:
                permissions = [
                    # 只读权限
                    'system:user:list', 'system:role:list',
                    # 个人管理权限
                    'system:user:profile',
                    # 聊天权限
                    'system:chat:use',
                ]
            
            user_data['permissions'] = permissions
            
            # 将权限保存到会话中以便前端访问
            return JsonResponse({
                'code': 200, 
                'user': user_data, 
                'permissions': permissions
            })
        except Exception as e:
            print(f"获取当前用户信息失败: {e}")
            return JsonResponse({'code': 500, 'msg': '获取用户信息失败'})


class RegisterView(APIView):
    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        email = data.get('email', '')  # 邮箱可选，默认为空字符串
        
        # 验证用户名是否已存在
        if SysUser.objects.filter(username=username).exists():
            return JsonResponse({'code': 500, 'info': '用户名已存在'})
            
        # 验证两次密码是否一致
        if password != confirm_password:
            return JsonResponse({'code': 500, 'info': '两次输入的密码不一致'})
            
        try:
            # 创建新用户
            user = SysUser(
                username=username,
                password=password,
                email=email,
                status=1,  # 1表示正常状态
                create_time=datetime.now(),
                avatar='default.jpg'
            )
            user.save()
            
            # 为新用户分配普通用户角色
            role = SysRole.objects.get(code='user')  # 获取普通用户角色
            user_role = SysUserRole(user_id=user.id, role_id=role.id)
            user_role.save()
            
            # 注册成功后直接登录
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            
            # 获取用户角色（新注册用户默认为普通用户）
            roleList = SysRole.objects.raw("select id, name, code from sys_role where code = 'user'")
            roles = ",".join([role.name for role in roleList])
            
            # 序列化用户数据
            user_data = SysUserSerializer(user).data
            user_data['roles'] = roles
            
            # 设置默认权限
            permissions = [
                'system:user:list',
                'system:role:list',
                'system:user:profile'
            ]
            
            return JsonResponse({
                'code': 200,
                'info': '注册成功',
                'token': token,
                'user': user_data,
                'permissions': permissions
            })
            
        except Exception as e:
            print(e)
            return JsonResponse({'code': 500, 'info': '注册失败，请稍后重试'})
