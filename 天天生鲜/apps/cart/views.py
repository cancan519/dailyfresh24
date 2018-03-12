from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
import json
# Create your views here.

class DeleteCartView(View):
    """删除购物车记录，一次删除一条"""
    def post(self,request):

        # 接收参数：sku_id
        sku_id = request.POST.get('sku_id')
        # 校验参数：not，判断是否为空
        if not sku_id:
            return JsonResponse({'code':1,'message':'sku_id为空'})
        # 判断用户是否登录
        try:
            GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'message': '删除的商品不存在'})
        # 如果用户登陆，删除redis中购物车数据
        if request.user.is_authenticated():
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            redis_conn.hdel('cart_%s' % user_id,sku_id)
        else:
        # 如果用户未登陆，删除cookie中购物车数据
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.loads(cart_json)
                # 删除字典中某个key及对应的内容
                del cart_dict[sku_id]
                # 将json转化成字符串
                new_cart_json = json.dumps(cart_dict)

                #将数据写入到cookie
                response = JsonResponse({'code': 0, 'message': '删除成功'})
                response.set_cookie('cart',new_cart_json)

                return response

        return JsonResponse({'code': 0, 'message': '删除成功'})
class UpdateCartView(View):
    """更新购物车信息"""
    def post(self,request):
        """实现增加与删除，并渲染到模板"""

        # 获取参数：sku_id, count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验参数all()
        if not all([sku_id,count]):
            return JsonResponse({'code':1,'massage':'缺少参数'})
        # 判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'massage': '商品不存在'})
        # 判断count是否是整数
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 3, 'massage': '商品数量错误'})
        # 判断库存
        if count >sku.stock:
            return JsonResponse({'code': 4, 'massage': '库存不足'})
        # 判断用户是否登陆
        if request.user.is_authenticated():
            # 如果用户登陆，将修改的购物车数据存储到redis中
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            # 因为是幂等的算法，所以只需要最终的结果，不需要计算
            redis_conn.hset('cart_%s' % user_id,sku_id,count)

            return JsonResponse({'code': 0, 'massage': '更新成功'})
        else:
            # 如果用户未登陆，将修改的购物车数据存储到cookie中
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

            cart_dict[sku_id] = count
            # 把cart_dict转化成字符串
            new_cart_json = json.dump(cart_dict)
            # 更新购物车的信息
            response = JsonResponse({'code': 0, 'massage': '更新成功'})
            response.set_cookie('cart',new_cart_json)

            return response


class CartInfoView(View):
    """购物车页面的展示"""
    def get(self,request):
        """查询登陆和未登录时购物车的数据，并渲染"""

        if request.user.is_authenticated():
            # 用户一登录查询redis中数据
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            # 如果字典是通过hgetall查找的，那么sku_id,count都是bytes类型的
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)

        else:
            # 用户未登陆时，查询cookies中的数据
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                # 如果cart_dict是通过cookie得到的，sku_id ,count都是str
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

        # 定义临时变量
        total_count = 0
        total_sku_amount = 0
        skus = []

        # cart_dict = {sku_id1:count1,sku_id2:count2....}
        for sku_id, count in cart_dict.items():
            try:  # 这个是查询sku的数据
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                continue  # 有异常  略过展示没有异常的数据
            # 统一count类型都为int类型，方便后续的计算与比较
            count = int(count)
            # 小计
            amount = count * sku.price

            # 提示python是动态语言，所以可以动态的给sku添加属性，存储count与amount

            sku.count = count
            sku.amount = amount
            #  记录sku
            skus.append(sku)
            # 总金额和总计
            total_count += count
            total_sku_amount += amount
        # 构造上下文
        context = {
            'skus':skus,
            'total_count':total_count,
            'total_sku_amount':total_sku_amount
        }

        # 渲染模板
        return render(request,'cart.html',context)

class AddCartView(View):
    """添加到购物车"""

    def post(self,request):
        """接收购物车参数，校验购物车参数，保存参数"""
        # 接收购物车的数据  sku——id   user_id count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验参数
        if not all([sku_id,count]):
            return JsonResponse({'code':2, 'message':'缺少参数'})

        # 判断sku_id 是否合法
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code':3, 'message':'商品不存在'})

        # 判断count是否合法
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 4, 'message': '商品数量是错误的'})

        # 判断库存是否超出
        if count >sku.stock:
            return JsonResponse({'code': 5, 'message': '库存不足'})


        if request.user.is_authenticated():
            # 保存购物车数据到redis
            user_id = request.user.id
            redis_count = get_redis_connection('default')
            # 在添加购物车之前判断商品是否已经存在，若果已经存在就累加，不存在就重新赋值
            origin_count = redis_count.hget('cart_%s' % user_id, sku_id)
            if origin_count is not None:
                count += int(origin_count)  #  redis 存储的数据是bytes类型的 在运算时我们需要转化类型

            redis_count.hset('cart_%s' % user_id, sku_id, count)

            # 再次判断库存是否超出
            if count > sku.stock:
                return JsonResponse({'code': 5, 'message': '库存不足'})

            # 查询购物车数量响应给前端
            cart_num = 0
            cart_dict = redis_count.hgetall('cart_%s' % user_id)
            for val in cart_dict.values():
                cart_num += int(val)
            # 响应结果
            return JsonResponse({'code': 0, 'message': '添加成功', 'cart_num':cart_num})

        else:
            # 保存购物车数据到cookie中
            # 读取cookie中购物车数据
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                # 把cart_json转成字典
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}   # 为了后面继续方便操作购物车，这里定义空字典

            # 判断要存储的商品信息是否存在，如果已经存在就累加，反之，就给新值
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]  # 在json中，数据类型不变  这里是取出sku_id的oringin_count
                count += origin_count

            # 再次判断库存是否超出
            if count > sku.stock:
                return JsonResponse({'code': 5, 'message': '库存不足'})

            # 把最新的商品的数量赋值给购物车字典
            cart_dict[sku_id] = count  # 这里是取出sku_id的oringin_count 赋值到字典中

            # 在写入cookie中，将cart_dict转字典
            new_cart_json = json.dumps(cart_dict)

            # 查询购物车数量响应给前端，为了方便前端查询后端添加购物车成功后的页面，需要查询购物车
            cart_num = 0
            for val in cart_dict.values():
                cart_num += val  # val是json转过来的，是int类型，不需要转化类型

            # 创建response
            response = JsonResponse({'code': 0, 'message': '添加购物车成功','cart_num':cart_num})

            # 写入cookie
            response.set_cookie('cart',new_cart_json)

            return response
