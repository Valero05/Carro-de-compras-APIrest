from django.shortcuts import render
from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from .serializers import *
from.models import *
from .paginations import *
from .permissions import *
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group
from datetime import date
import math
# Create your views here.

class CategoryView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes =[]


class MenuItemView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['category', 'price']
    search_fields = ['title', 'category__title']
    pagination_class = MenuPagination
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class SingleMenuItemView(generics.RetrieveUpdateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsManager|IsAdminUser]
        return [permission() for permission in permission_classes]
    def patch(self, request, *args, **kwargs):
        menuitem = MenuItem.objects.get(pk=self.kwargs['pk'])
        menuitem.featured = not menuitem.featured
        menuitem.save()
        return JsonResponse( status=200, data={'message':'Featured status of {} changed to {}'.format(str(menuitem.title), str(menuitem.featured))})
    

class ManagersView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = ManagerListingSerializer
    permission_classes = [IsAuthenticated, IsManager|IsAdminUser]

    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)
            return JsonResponse(status=201, data={'message':'User added to managers group'})
        

class ManagerRemoveView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = ManagerListingSerializer
    permission_classes = [IsAuthenticated, IsManager|IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name='Manager')
        managers.user_set.remove(user)
        return JsonResponse(status=200, data={'message':'User removed from managers Group'})

class DeliveryCrewView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='delivery_crew')
    serializer_class = ManagerListingSerializer
    permission_classes = [IsAuthenticated, IsManager|IsAdminUser]

    def post(self, request, *args, **kwargs):
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            crew = Group.objects.get(name='delivery_crew')
            crew.user_set.add(user)
            return JsonResponse(status=201, data={'message':'User added to delivery crew'})
            
class DeliveryRemoveView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = ManagerListingSerializer
    permission_classes = [IsAuthenticated, IsManager|IsAdminUser]
    queryset = User.objects.filter(groups__name='delivery_crew')

    def destroy(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        crew = Group.objects.get(name='delivery_crew')
        crew.user_set.remove(user)
        return JsonResponse(status=200, data={'message':'User removed from Delivery Crew'})


class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart = Cart.objects.filter(user=self.request.user)
        return cart
    def post(self, request, *args, **kwargs):
        serialized_item = CartAddSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        id = request.data['menuitem']
        quantity = request.data['quantity']
        item  = get_object_or_404(MenuItem, id=id)
        price = int(quantity)*item.price
        try:
            Cart.objects.create(user=request.user, quantity=quantity, unit_price=item.price, price=price, menuitem_id=id)
        except:
            return JsonResponse(status=409, data={'message':'Item already in cart'})
        return JsonResponse(status=201, data={'message':'Item added to cart.'})
    
    def destroy(self, request, *args, **kwargs):
       # if self.kwargs['pk']:
        #    serialized_item = CartRemoveSerializer(data=request.data)
          #  serialized_item.is_valid(raise_exception=True)
         #   cart=get_object_or_404(Cart, user=request.user, menuitem=self.kwargs['pk'])
           # cart.delete()
            #return JsonResponse(status=200, data={'message':'Item removed from cart.'})
        #else:
            Cart.objects.filter(user=request.user).delete()
            return JsonResponse(status=200, data={'message':'All items removed from cart'})
        

class OrderView(generics.ListCreateAPIView):
    throttle_classes=[AnonRateThrottle, UserRateThrottle]
    serializer_class=OrderSerializer
    def get_queryset(self):
       if self.request.user.groups.filter(name='Manager').exists()|self.request.user.is_superuser == True:
           query=Order.objects.all()
       elif self.request.user.groups.filter(name='delivery_crew').exists():
           query=Order.objects.filter(delivery_crew=self.request.user)
       else:
           query=Order.objects.filter(user=self.request.user)
       return query
    def get_permissions(self):
        if self.request.method == 'GET' or 'POST':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes=[IsAuthenticated, IsManager|IsAdminUser]
        return[permission() for permission in permission_classes]
    def post(self, request, *args, **kwargs):
        cart=Cart.objects.filter(user=request.user)
        cartsize=cart.values_list()
        if len(cartsize)==0:
            return HttpResponseBadRequest
        total = math.fsum([float(cartsize[-1]) for cartsize in cartsize])
        order = Order.objects.create(user=request.user, status=False, total=total, date=date.today())
        for item in cart.values():
            menuitem = get_object_or_404(MenuItem, id=item['menuitem_id']) 
            orderitem = OrderItem.objects.create(order=order, menuitem=menuitem, quantity=item['quantity'], unit_price=item['unit_price'], price=item['price'])
            orderitem.save()
        cart.delete()
        return JsonResponse(status=201, data={'message':'Your order has been placed. Your order number is {}'.format(str(order.id))})
    


class OrderItemView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderItemSerializer
      
    def get_permissions(self, *args, **kwargs):
        order= Order.objects.get(pk=self.kwargs['pk'])
        if self.request.user==order.user and self.request.method=='GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method=='PUT' or self.request.method=='DELETE':
            permission_classes=[IsAuthenticated, IsAdminUser|IsManager]
        else:
           permission_classes=[IsAuthenticated, IsDeliveryCrew|IsManager|IsAdminUser]
        return [permission() for permission in permission_classes]
    def get_queryset(self, *args, **kwargs):
        query = Order.objects.filter(id=self.kwargs['pk'])
        return query

    def patch(self, request, *args, **kwargs):
        order=Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()
        return JsonResponse(status=200, data={'message':'Status of order #{} changed to {}'.format(str(order.id),str(order.status))})
    
    def put(self, request, *args, **kwargs):
        serialized_item=OrderAddSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        order_pk=self.kwargs['pk']
        crew_pk=request.data['delivery_crew']
        order=get_object_or_404(Order, pk=order_pk)
        crew=get_object_or_404(User, pk=crew_pk)
        order.delivery_crew=crew
        order.save()
        return JsonResponse(status=201, data={'message':'{} was assigned to order #{}'.format(str(crew.username),str(order.id))})
    
    def destroy(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order_nummber = str(order.id)
        order.delete()
        return JsonResponse(status=200, data={'message':'Order #{} was deleted.'.format(order_nummber)})
    