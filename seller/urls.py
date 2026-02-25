from django.urls import path
from . import views
urlpatterns = [
          path("usersellerbridge/",views.user_seller_bridge,name="user_seller"),

]