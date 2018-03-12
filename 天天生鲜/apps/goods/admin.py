from django.contrib import admin
from goods.models import  GoodsCategory, Goods, IndexPromotionBanner
from celery_tasks.tasks import genrate_static_index_html
# Register your models here.

class BaseAdmin(admin.ModelAdmin):
    """下面的方法是父类ModelAdmin中的，父类没有异步的方法，我们重写方法"""

    def save_model(self, request, obj, form, change):
        # 调用父类的逻辑  实现保存
        obj.save()
        # 触发生成静态页面的异步任务
        genrate_static_index_html.delay()

    def delete_model(self, request, obj):
        # 调用父类的逻辑  实现保存
        obj.delete()
        genrate_static_index_html.delay()

    """运维操作活动页面"""
class IndexPromotionBannerAdmin(admin.ModelAdmin):

   pass


class GoodsCategoryAdmin(BaseAdmin):
    pass


class GoodsAdmin(BaseAdmin):
    pass


admin.site.register(GoodsCategory,GoodsCategoryAdmin)
admin.site.register(Goods,GoodsAdmin)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)