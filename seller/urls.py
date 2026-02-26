from django.urls import path
from . import views
urlpatterns = [
          path("usersellerbridge/",views.user_seller_bridge,name="user_seller"),
          path("sellerregistration/",views.seller_registration,name="seller_registration"),

]