from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.views.generic import View
from django.core.urlresolvers import reverse
import re
from django import db
from users.models import User,Address
from celery_tasks.tasks import send_active_email
# Create your views here.
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from itsdangerous import SignatureExpired
from django.contrib.auth import authenticate, login, logout
from utils.views import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU
import json

class UserInfoView(LoginRequiredMixin,View):
    """个人信息"""
    def get(self,request):
        """查询基本信息与最近浏览记录，并且渲染"""
        # 查询基本信息  用户名+联系方式+地址
        user = request.user
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            # 将来在模板中判断地址是否为空，如果为空，相对应的html不写
            address = None
        # 查询最近浏览
        # 使用Django_redis 操作reids  创建一个redis对象
        redis_conn = get_redis_connection('default')
        # 调用对应的方法 查询redis列表中保存的sku_ids
        sku_ids = redis_conn.lrange('history_%s' % user.id,0,4)
        # 遍历sku_ids 取出sku_id
        sku_list = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            sku_list.append(sku)
        # 构造上下文
        context = {
            'address':address,
            'sku_list':sku_list
        }
        # 渲染模板
        return render(request,'user_center_info.html',context)


class AddressView(LoginRequiredMixin, View):
  """用户地址"""

  def get(self, request):
      """提供用户地址页面"""
      # 获取登陆用户
      user = request.user
      # 查询用户登陆的地址信息  查询用户最近创建的地址信息  取最新的地址信息
      # 一：下面是简单的获取的方法
      # address_list = Address.objects.filter(user=user)[-1]
      # 二：利用ordeby 再次获取  order_by 可以按照时间倒叙  取第0个
      # address= Address.objects.filter(user=user).order_by('-create_time')[0]
      # 三：最简单的  address_set是一个关联的模型类   latest默认倒叙，取出第0个
      try:
          address = user.address_set.latest('create_time')
      except Address.DoesNotExist:
          # 将来在模板中判断地址是否为空，如果为空，相对应的html不写
          address = None

      # 构造上下文
      context = {
         # 'user':user, #user信息不需要传递，因为下面调用了request中就包含了user
        'address':address
        }
      # 渲染模板
      return render(request, 'user_center_site.html',context)


  def post(self, request):
      """修改地址信息"""

    # 接收地址信息参数
      recv_name = request.POST.get('recv_name')
      addr = request.POST.get('addr')
      zip_code = request.POST.get('zip_code')
      recv_mobile = request.POST.get('recv_mobile')
    # 地址校验
    #   说明  实际上 开发需要校验数据是否真实，比如手机号，邮编是否是符合规定的
      if all([recv_name,addr,zip_code,recv_mobile]):
    # 保存参数
          Address.objects.create(
              user=request.user,
              receiver_name = recv_name,
              receiver_mobile = recv_mobile,
              detail_addr = addr,
              zip_code = zip_code
          )

    #响应
      return redirect(reverse('users:address'))

class LogoutView(View):
    def get(self,request):
        logout(request)
        # return redirect(reverse('users:login'))
        return redirect(reverse('goods:index'))

class LoginView(View):
    """登陆"""
    def get(self,request):
        """提供登陆页面"""
        return render(request,'login.html')

    def post(self, request):
        """处理登陆逻辑"""
#     接受登陆请求参数
        user_name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
#       校验登陆请求参数
        if not all([user_name, pwd]):
            # 判断是否有
            return redirect(reverse('users:login'))

#         判断是否存在  authenticate属性就是判断是否存在
        user = authenticate(username=user_name, password=pwd)
        print(user)
        if user is None:
            # 提示用户：用户名或者密码错误
            return render(request, 'login.html', {'errmsg':'用户名或者密码错误'})

        # 判断用户是否是激活用户
        if user.is_active == False:
            # 提示用户激活
            return render(request,'login.html',{'errmsg':'请激活'})

        # 登陆用户 主要是生成状态保持数据，并默认写入到django——session表中
        # 如果调用login方法 没有指定SESSION_ENGINE,那么就默认存到django—session中
        # 指定了之后，就按照引擎的指引进行session数据的存储，需要搭配djan——redis使用
        login(request, user)

#         记住用户名  多少天免登陆   如果用户勾选了‘记住用户名’，就把状态保持，反之保持0秒
        remembered = request.POST.get('remembered')
        if remembered != 'on':
            request.session.set_expiry(0)  #没有勾选  保持0秒
        else:
            request.session.set_expiry(60*60*24*10)  #保持10天

        # 在界面跳转以前，将cookie中的购物车合并到redis中
        cart_json = request.COOKIES.get('cart')
        if cart_json is not None:
            # cookie中得捣的key是str，val是int
            cart_dict_cookie = json.loads(cart_json)
        else:
            cart_dict_cookie = {}

        # 查询redis中的购物车信息
        redis_coon = get_redis_connection('default')
        # 通过django——redis得捣的key和val都是bytes类型的
        cart_dict_redis = redis_coon.hgetall('cart_%s' % user.id)

        # 遍历cart_dict_cookie，取出sku_id,count信息
        for sku_id,count in cart_dict_cookie.items():
            sku_id = sku_id.encode()  # 将 str转化成bytes类型
            if sku_id in cart_dict_redis:
                origin_count = cart_dict_redis[sku_id]
                count += int(origin_count)

                # # 在这里合并可能造成库存不足
                # sku = GoodsSKU.objects.get(id=sku_id)
                # if count > sku.stock:
                #     pass   #这个只可能是在这里出现，一般情况只有在登陆的时候才会查询购物车信息，所以这里不做解释

            # 保存合并的数据到redis
            cart_dict_redis[sku_id] = count
        # 一次性向redis中添加数据
        if cart_dict_redis:
            redis_coon.hmset('cart_%s' % user.id, cart_dict_redis)

        # 在界面跳转以前，判断，有next就跳转next，没有就转到主页
        next = request.GET.get('next')
        if next is None:
            # 响应结果
            response =redirect(reverse('goods:index')) #跳转到主页
        else:
            # 这里添加一个跳转的问题，这里只接受post
            if next == '/orders/place':
                response = redirect(reverse('cart:info'))
            else:
                 response =redirect('/orders/place')

        # 删除cookie中的数据
        response.delete_cookie('cart')

        return response

class ActiveView(View):
    """邮件激活"""
    # http://127.0.0.1:8000/users/active/djf@#$^&HSHDF×（
    def get(self,request,token):

        # 获取封装了user_id的字典
        # 创建序列化  注意  调用loads方法的序列化器的参数要和调用dumps方法时的参数一致
        serializer = Serializer(settings.SECRET_KEY, 3600)

        #解出原始的字典 {"confirm": self.id}
        # loads()解出token字符串，得到用户id明文
        try:
            result =serializer.loads(token)
        except SignatureExpired:  #签名过期的异常
            return HttpResponse ('激活链接已过期')
        # 获取user_id
        user_id = result.get('confirm')
        # 查询user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:  #查询结果不存在的异常
            return HttpResponse('用户不存在')
        # 重置激活状态为True
        user.is_active = True
        # 一定要记得手动保存
        user.save()
        # 响应结果
        return redirect(reverse('users:login'))


class RegisterView(View):
    """类视图，注册，提供注册页面和实现注册逻辑"""
    def get(self,request):
        return render(request, 'register.html')

    def post(self,request):
        # 接受用户注册参数
        user_name = request.POST.get('user_name')
        pwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验用户注册参数
        # 只要有一个数据为空，就返回假，只有全部为真则为真
        if not all([user_name,pwd,email]):
            # 公司中，根据开发文档实现需求
            return redirect(reverse('users:register'))

        # 判断邮箱格式
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
             return render(request, 'register.html', {'errmsg':'邮箱格式错误'})

        # 是否勾选了同意
        # on == 勾选
        if allow != 'on':
            return render(request,'register.html',{'errmsg':'请勾选用户协议'})
        # 保存用户注册参数
        # 以下的代码不用调用save保存（只有使用，user.object.create()或者user.
        try:
            user = User.objects.create_user(user_name, email, pwd)
        #重名异常判断
        except db.IntegrityError:
            return render(request,'register.html',{'errmsg':'用户已存在'})
        # 重置激活的状态
        user.is_active = False
        # 注意：重置之后需要重新保存一下，每次调用模型类改动时，都需要保存
        # 还可以使用creat（），但是都需要调用save保存
        user.save()

        # 发送激活邮件
        # 把激活状态变为TURE
        # 生成token
        token = user.generate_active_token()

        # 异步发送邮件，生成token 响应之前 发送邮件，激活
        # 在这里有个delay  就是用于触发异步任务的
        send_active_email.delay(email,user_name,token)

        return redirect(reverse('goods:index'))

# def register(request):
#     #注册,提供注册页面与逻辑
#     # 如果在一个视同中，实现多种请求逻辑，请求地址使用相同的地址，只是请求方法不同
#     if request.method == 'GET':
#         return render(request,'register.html')
#     if request.method =='POST':
#         return HttpResponse ('这里是请求逻辑')