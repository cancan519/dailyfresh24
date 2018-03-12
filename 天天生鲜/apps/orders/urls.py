from django.conf.urls import url
from orders import views

urlpatterns = [

    # 订单确认 http://127.0.0.1:8000/orders/place
    url(r'^place$',views.PlaceOrderView.as_view(),name='place')

]