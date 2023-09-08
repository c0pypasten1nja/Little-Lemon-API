from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:id>', views.SingleMenuItemView.as_view()),
    path('groups/manager/users', views.UserGroupManagerView.as_view()),
    path('groups/manager/users/<int:id>',
         views.SingleUserGroupManagerView.as_view()),
    path('groups/delivery-crew/users', views.UserGroupDeliveryCrewView.as_view()),
    path('groups/delivery-crew/users/<int:id>',
         views.SingleUserGroupManagerView.as_view()),
    path('cart/menu-items', views.CartManagementView.as_view()),
    path('orders', views.OrderListCreateView.as_view()),
    path('orders/<int:id>', views.OrderDetailView.as_view()),

]
