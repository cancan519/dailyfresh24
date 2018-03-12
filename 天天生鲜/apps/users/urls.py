from django.conf.urls import url
from users import views
# from django.contrib.auth.decorators import login_required
urlpatterns = [
    # 函数注册页面的路径匹配
    # url(r'^register$',views.register)
    # 类视图注册页面的路径匹配
    url(r'^register$',views.RegisterView.as_view(),name='register'),

    # http://127.0.0.1:8000/users/active//djf@#$^&HSHDF×
    url(r'^active/(?P<token>.+)$',views.ActiveView.as_view(),name='active'),

#     登陆http://127.0.0.1:8000/users/login
    url(r'^login$',views.LoginView.as_view(),name='login'),

    # 退出登陆
    url(r'^logout$',views.LogoutView.as_view(),name='logout'),

    #收货地址
    url(r'^address$',views.AddressView.as_view(),name='address'),
    #个人信息
    url(r'^info$',views.UserInfoView.as_view(),name='info')
]