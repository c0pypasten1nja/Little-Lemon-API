from rest_framework import generics
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, UserSerializer, User, CartSerializer, CartAddSerializer, OrderSerializer
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

samples = "Please restart your device and try again!"

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get(self, request):
        if not request.user.has_perm('LittleLemonAPI.view_menuitem'):
            return Response(samples, status=status.HTTP_401_UNAUTHORIZED)
        menu_items = self.get_queryset()
        serializer = self.serializer_class(menu_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SingleMenuItemView(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin,
                         generics.GenericAPIView):
    serializer_class = MenuItemSerializer
    lookup_url_kwarg = 'id'
    queryset = MenuItem.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UserGroupManagerView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request):
        if not request.user.groups.filter(name="Manager"):
            return Response(samples, status=status.HTTP_401_UNAUTHORIZED)
        managers = self.queryset.filter(groups=3)
        serializer = self.serializer_class(managers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name="Manager")
            managers.user_set.add(user)
            return JsonResponse(status=201, data={'message': 'User added to Manager group'})


class SingleUserGroupManagerView(generics.DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=self.kwargs['id'])
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        return JsonResponse(status=200, data={'message': 'User removed from Managers group'})


class UserGroupDeliveryCrewView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request):
        if not request.user.groups.filter(name="Manager"):
            return Response(samples, status=status.HTTP_401_UNAUTHORIZED)
        crews = self.queryset.filter(groups=2)
        serializer = self.serializer_class(crews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            crews = Group.objects.get(name="Delivery crew")
            crews.user_set.add(user)
            return JsonResponse(status=201, data={'message': 'User added to Delivery crew group'})


class SingleUserGroupDeliveryCrewView(generics.DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=self.kwargs['id'])
        crews = Group.objects.get(name="Delivery crew")
        crews.user_set.remove(user)
        return JsonResponse(status=200, data={'message': 'User removed from Delivery crew group'})


class CartManagementView(generics.ListCreateAPIView,
                         mixins.DestroyModelMixin):
    serializer_class = CartSerializer

    def get_queryset(self, *args, **kwargs):
        cart = Cart.objects.filter(user=self.request.user)
        return cart

    def post(self, request, *arg, **kwargs):
        serialized_item = CartAddSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        menuitem_id = request.data['menuitem']
        quantity = request.data['quantity']
        item = get_object_or_404(MenuItem, id=menuitem_id)
        price = int(quantity) * item.unit_price
        Cart.objects.create(user=request.user, quantity=quantity,
                            unit_price=item.unit_price, price=price, menuitem_id=menuitem_id)
        return JsonResponse(status=201, data={'message': 'Item added to cart!'})

    def delete(self, request, *arg, **kwargs):
        Cart.objects.filter(user=request.user).delete()
        return JsonResponse(status=201, data={'message': 'All Items removed from cart'})
    
    
class OrderListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.all()  # This will return all orders for authorized users
    
    def post(self, request, *args, **kwargs):
        
        # Calculate the total cost of the order based on the cart items
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            raise NotFound("No items in the cart to create an order.")
        
        total = sum(item.menuitem.unit_price * item.quantity for item in cart_items)

        order = Order(user=request.user, total=total)
        order.save()
        for cart_item in cart_items:
            order_item = OrderItem(order=order, menu_item=cart_item.menuitem, quantity=cart_item.quantity)
            order_item.save()
            cart_item.delete()
        
        serializer = self.serializer_class(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return Order.objects.all()

    def get(self, request, *args, **kwargs):
        order = self.get_object()
        
        # Check if the order belongs to the current user
        if request.user.groups.filter(name="Customer").exists() and order.user != request.user:
            return Response(samples, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = self.serializer_class(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        order = self.get_object()
        # Check if a manager is updating the order
        if request.user.groups.filter(name="Manager").exists():
            # Additional validation logic for setting delivery crew and order status
            if 'delivery_crew' in request.data and 'order_status' in request.data:
                order_status = request.data['order_status']
                crew = get_object_or_404(User, pk=request.data['delivery_crew'])
                if crew and int(order_status) in [0, 1]:
                    order.delivery_crew = crew
                    order.order_status = order_status
                    order.save()
                    
                    serializer = self.serializer_class(order)
                    return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        
        # Check if a delivery crew is updating the order status
        if request.user.groups.filter(name="Delivery crew").exists() and 'order_status' in request.data:
            order_status = request.data['order_status']

            if int(order_status) in [0, 1]:
                order.order_status = order_status
                order.save()
                serializer = self.serializer_class(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(samples, status=status.HTTP_401_UNAUTHORIZED)
        
        return super().partial_update(request, *args, **kwargs)


    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        
        # Check if a manager is deleting the order
        if not request.user.groups.filter(name="Manager").exists():
            return Response(samples, status=status.HTTP_401_UNAUTHORIZED)
        
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
