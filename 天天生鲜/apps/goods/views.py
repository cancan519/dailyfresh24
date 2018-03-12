from django.shortcuts import render,redirect
from django.views.generic import View
from goods.models import GoodsCategory, Goods, GoodsSKU, IndexGoodsBanner, IndexCategoryGoodsBanner, IndexPromotionBanner
from django.core.cache import cache
from django_redis import get_redis_connection
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage
import json

# Create your views here.

class BaseView(View):
    """查询登陆或者未登录购物车的数据"""

    def get_cart_num(self,request):

        cart_num = 0
        # 如果是登陆用户才能查看购物车，判断登陆
        if request.user.is_authenticated():
            # 创建redis对象，有个get_redis_connection方法,有个参数‘delfault’
            redis_conn = get_redis_connection('default')
            # 调用hgetall(), 获取所有购物车的数据
            user_id = request.user.id
            cart_dict = redis_conn.hgetall('cart_%s' % user_id)

            # 遍历cart_dic，获取数量，累加求和 说明：在hgetall（）返回的字典中，
            # 里面的key和value都是字节类型的，需要转化类型
            for val in cart_dict.values():
                cart_num += int(val)  # 因为val是字节类型的，cart_num是字节类型的，所以需要转化成int
        else:
            # cookie存储的是json的字符串
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}
            # 遍历cart_dict,取出count求和
            for val in cart_dict.values():
                cart_num += val

        return cart_num


class listView(BaseView):
    """列表页"""
    def get(self,request,category_id,page_num):
        """查询数据，渲染模板，实现分页和排序"""
        # 获取排序的sort：提示  如果用户不穿sort，给默认值即可
        sort = request.GET.get('sort','default')

        # 查询用户看的商品的分类，category对应的分类
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))
        # 查询所有的商品分类
        categorys = GoodsCategory.objects.all()
        # 查询新品的推荐
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]
        # 查询categery对应的sku,并且排序
        if sort == 'price':  # 价格从低到高
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':   # 销量由高到底排序
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:  # 如果出现/list/1/1？sort=jfjaef jj fjaosfj  乱码
            skus = GoodsSKU.objects.filter(category=category)
            sort = 'default'  # 因为sort后期要传给模板，我需要重置sort
        # 查询购物车信息
        cart_num = self.get_cart_num(request)

        # 查询分页的数据  paginator
        # （因为查出来的数据非常多，所以我们在构造上下文之前做个分页）
        # 回顾django基础中，Paginator有init方法有两个参数，第一个是要分页的列表，第二个是每页几个
        paginator = Paginator(skus,2)
        # 获取用户要看的哪一页\
        page_num=int(page_num)
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:  #  如果遇到不法分子  就将它转到第一页
            page_skus = paginator.page(1)
        # 获取页码列表
        page_list = paginator.page_range

        # 构造上下文
        context = {
            'category':category,
            'categorys':categorys,
            'new_skus':new_skus,
            'page_skus':page_skus,
            'page_list':page_list,
            'sort':sort,
            'cart_num':cart_num
        }
        # 渲染模板
        return render(request,'list.html',context)

class DetailView(BaseView):
    """详情"""
    def get(self,request,sku_id):
        """查询详情页，并且渲染模板"""
        # 用户 就在request中，不需要再次查询
        # 查询商品的sku信息
        try:
            sku= GoodsSKU.objects.get(id=sku_id)
        except GeneratorExit:
            return redirect(reverse('goods:index'))
        # 查询商品的分类信息
        Category=GoodsCategory.objects.all()

        # 商品的评价
        sku_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]
        if sku_orders:
            for sku_order in sku_orders:
                sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                sku_order.username = sku_order.order.user.username
        else:
            sku_orders = []
        # 查询最近推荐的信息
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]

        # 查询其他规格商品 exclude()
        # GoodsSKU.objects.exclude(id=sku.id)   #这个能其他商品类，所以不能这么简单
        # 我们可以查询sku的spu信息，然后可以过滤到其他商品类  sku.goods=spu  spu.goodssku_set()点出外键
        # spu.goodssku_ste.exclude()  这样才可以查出来只有除了这个商品的其他的规格
        other_skus = sku.goods.goodssku_set.exclude(id=sku.id)

        # 查询购物车信息
        cart_num = cart_num = self.get_cart_num(request)
        # 如果是登陆用户才能查看购物车，判断登陆
        if request.user.is_authenticated():
            # 创建redis对象，有个get_redis_connection方法,有个参数‘delfault’
            redis_conn = get_redis_connection('default')
            # 调用hgetall(), 获取所有购物车的数据
            user_id = request.user.id

            # 记录浏览信息 lpush(存储）
            # 在这里先去除重复
            redis_conn.lrem('history_%s' % user_id,0,sku_id)
            # 然后添加
            redis_conn.lpush('history_%s' % user_id,sku_id)
            # 然后去中间的5个
            redis_conn.ltrim('history_%s' % user_id,0, 4)

        # 构造上下文
        context = {
            'sku':sku,
            'Category':Category,
            'sku_orders':sku_orders,
            'new_skus':new_skus,
            'other_skus':other_skus,
            'cart_num':cart_num
        }

        #渲染模板
        return render(request,'detail.html',context)

class IndexView(BaseView):
    """主页"""
    def get(self,request):
        """查询主页商品的数据，并且渲染"""
        context = cache.get('index_page_data')

        if context is None:
            print('没有缓存，查询数据')
            # 查询用户user信息  不需要查询，他在quest中
            # 查询商品分类信息
            categorys = GoodsCategory.objects.all()
            # 查询图片轮播信息,需求，根据index从小到大排序
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')
            # 查询商品活动信息 需求，根据index从小到大排序
            promotionBanners = IndexPromotionBanner.objects.all().order_by('index')

            # 查询主页商品分类列表信息
            for category in categorys:
                title_banners = IndexCategoryGoodsBanner.objects.filter(category=category,display_type=0)
                category.title_banners = title_banners

                image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1)
                category.image_banners = image_banners


            # 构造上下文
            context = {
                'categorys':categorys,
                'goods_banners':goods_banners,
                'promotionBanners':promotionBanners,
            }
            # 缓存上下文，缓存的key ，缓存的数据，过期的秒数（运维会给需求）
            cache.set('index_page_data', context, 3600)
        # 查询购物车信息
        cart_num = self.get_cart_num(request)

        # 更新context
        context.update(cart_num=cart_num)
        # 渲染模板
        return render(request,'index.html', context)