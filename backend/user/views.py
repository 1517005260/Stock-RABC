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
from role.models import SysRole, SysUserRole
from user.models import SysUser, SysUserSerializer


# @method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):

    def post(self, request):
        username = request.GET.get("username")
        password = request.GET.get("password")
        try:
            user = SysUser.objects.get(username=username, password=password)
            
            # 检查用户状态，只允许正常状态（status=1）的用户登录
            if user.status == 0:
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
            
            # 将用户数据序列化
            user_data = SysUserSerializer(user).data
            # 添加角色信息到用户数据
            user_data['roles'] = roles
            
            # 添加权限信息
            permissions = []
            is_admin = False
            
            # 检查是否是管理员角色
            for role in roleList:
                if role.code == 'admin' or role.name == '管理员':
                    is_admin = True
                    break
            
            # 如果是管理员，添加所有权限
            if is_admin:
                # 这里添加所有系统权限标识符
                permissions = [
                    'system:user:list', 'system:user:edit', 'system:user:remove', 'system:user:reset',
                    'system:role:list', 'system:role:edit', 'system:role:remove',
                    'system:menu:list', 'system:menu:edit', 'system:menu:remove'
                ]
            else:
                # 这里应该基于角色获取实际权限
                # 临时允许基本权限，后续可以完善
                permissions = ['system:user:list', 'system:role:list']

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
        if data['id'] == -1:  # 添加
            obj_sysUser = SysUser(username=data['username'], password=data['password'], email=data['email'],
                                  phonenumber=data['phonenumber'], status=data['status'], remark=data['remark'])
            obj_sysUser.create_time = datetime.now()
            obj_sysUser.avatar = 'default.jpg'
            obj_sysUser.password = '123456'

            obj_sysUser.save()
        else:  # 修改
            obj_sysUser = SysUser(id=data['id'], username=data['username'], password=data['password'],
                                  avatar=data['avatar'], email=data['email'], phonenumber=data['phonenumber'],
                                  login_date=data['login_date'], status=data['status'], create_time=data['create_time'],
                                  update_time=data['update_time'], remark=data['remark'])
            obj_sysUser.update_time = datetime.now()
            obj_sysUser.save()
            
            # 获取用户角色信息，添加到响应中
            user_data = SysUserSerializer(obj_sysUser).data
            try:
                roleList = SysRole.objects.raw("select id, name from sys_role where id in (select role_id from "
                                              "sys_user_role where user_id=" + str(data['id']) + ")")
                roles = ",".join([role.name for role in roleList])
                user_data['roles'] = roles
                return JsonResponse({'code': 200, 'user': user_data})
            except Exception as e:
                print(f"获取用户角色失败: {e}")

        return JsonResponse({'code': 200})

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
            user_data['roles'] = roles
            
            # 添加权限信息
            permissions = []
            is_admin = False
            
            # 检查是否是管理员角色
            for role in roleList:
                if role.code == 'admin' or role.name == '管理员':
                    is_admin = True
                    break
            
            # 如果是管理员，添加所有权限
            if is_admin:
                # 这里添加所有系统权限标识符
                permissions = [
                    'system:user:list', 'system:user:edit', 'system:user:remove', 'system:user:reset',
                    'system:role:list', 'system:role:edit', 'system:role:remove',
                    'system:menu:list', 'system:menu:edit', 'system:menu:remove'
                ]
            else:
                # 这里应该基于角色获取实际权限
                # 临时允许基本权限，后续可以完善
                permissions = ['system:user:list', 'system:role:list']
            
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
