from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.MenuItemView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('category', views.CategoryView.as_view()),
    path('cart/menu-items', views.CartView.as_view()),
    path('groups/managers/users', views.ManagersView.as_view()),
    path('groups/managers/users/<int:pk>', views.ManagerRemoveView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryCrewView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryRemoveView.as_view()),
    path('orders', views.OrderView.as_view()),
    path('orders/<int:pk>', views.OrderItemView.as_view()),
]