from django.shortcuts import render,redirect
from django.views.generic import View
from utils.views import LoginRequiredMixin
from django.core.urlresolvers import reverse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from users.models import Address
# Create your views here.


class PlaceOrderView(LoginRequiredMixin,View):
    """的订单确认"""
    def post(self,request):
        """购物和去结算和详情页立即购买进入订单详情页"""
        # 判断用户是否登陆：LoginRequiredMixin
        # 获取参数：sku_ids, count
        sku_ids = request.POST.getlist('sku_ids')  # 一键多值的情况
        count = request.POST.get('count')

        # 校验sku_ids参数：not
        if not sku_ids:
            return redirect(reverse('cart:info'))

        # 定义临时的变量
        skus = []
        total_sku_amount = 0
        total_count = 0
        trans_cost = 10  # 邮费默认是10
        # 校验count参数：用于区分用户从哪儿进入订单确认页面
        if count is None:
            # 如果是从购物车页面去结算过来

            # 商品的数量从redis中获取
            redis_conn = get_redis_connection('default')
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)

            for sku_id in sku_ids:
                 # 查询商品的信息  # 查询商品数据 sku -->sku_id<---sku_ids
                 # 提醒：sku_ids是字符串类型
                try:
                    sku =GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))

                # 得捣商品的数量  默认是bytes类型的  所以转化一下
                sku_count = cart_dict[sku_id.encode()]
                sku_count = int(sku_count)

                # 计算小计
                amount = sku_count * sku.price

                # 动态的给sku对象绑定count和 amount
                sku.count = sku_count
                sku.amount = amount
                # 记录sku
                skus.append(sku)

                #累加小计与金额
                total_count += sku_count
                total_sku_amount += amount

        else:

            # 如果是从详情页面过来
            for sku_id in sku_ids:
                # 查询商品的sku
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except GoodsSKU.DoesNotExist:
                    return redirect(reverse('cart:info'))

                # 商品的数量从request中获取,并try校验、
                try:
                    sku_count = int(count)
                except Exception:
                    return redirect(reverse('goods:detail',args=(sku_id,)))

                # 判断库存：立即购买没有判断库存
                if sku_count >sku.stock:
                    return redirect(reverse('goods:detail', args=(sku_id,)))
                # 计算小计
                amount = sku_count * sku.price

                # 动态的给sku对象绑定count和 amount
                sku.count = sku_count
                sku.amount = amount
                # 记录sku
                skus.append(sku)

                # 累加小计与金额
                total_count += sku_count
                total_sku_amount += amount

        # 计算实付款
        total_amount = total_sku_amount + trans_cost

        # 查询用户地址信息
        try:
            address = Address.objects.filter(user=request.user).latest('create_time')
        except Address.DoesNotExist:
            address =None
        # 构造上下文
        context={
            'skus':skus,
            'total_amount':total_amount,
            'total_count':total_count,
            'total_sku_amount':total_sku_amount,
            'address':address,
            'sku_ids':sku_ids,
            'trans_cost':trans_cost
        }
        # 响应结果:html页面
        return render(request,'place_order.html', context)
