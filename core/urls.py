from django.urls import path
from . import views
urlpatterns = [
    path("login/",views.login_view,name="login"),
    path("register/",views.register_view,name="register"),
    path("",views.home_view,name="home"),
    path("logout/",views.logout_view,name="logout"),
    path("products/", views.all_products, name="all_products"), 
    path("home/category/subcategory/<str:category_slug>/", views.subcategory_view,name="subcategory"),  
    path("home/category/subcategory/variants/<str:slug>/", views.product_detail,name="product_details"),  
    ]