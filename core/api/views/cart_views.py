import uuid

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from core.api.serializers.cart_serializers import CartSerializer
from core.api.views.user_views import UserDetailView
from core.models import Cart, Item, WashCategory


@extend_schema(tags=['Cart'])
class CartListCreateView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @staticmethod
    def item_price(item_id: uuid.UUID) -> float:
        item = Item.objects.get(pk=item_id)
        return item.price

    @staticmethod
    def wash_category_price(wash_category_id: uuid.UUID) -> float:
        wash_category = WashCategory.objects.get(pk=wash_category_id)
        return wash_category.extra_per_item

    @staticmethod
    def calculate_price(item_id: uuid.UUID, wash_category_id: uuid.UUID, quantity: int) -> float:
        return (CartListCreateView.item_price(item_id) +
                CartListCreateView.wash_category_price(wash_category_id)) * quantity

    def post(self, request, *args, **kwargs):
        user = request.user
        item_id = request.data.get('item')
        wash_category_id = request.data.get('wash_category')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = int(request.data.get('quantity', 1))

        calculated_price = CartListCreateView.calculate_price(item_id, wash_category_id, quantity)
        UserDetailView.update_user_total_price(user, calculated_price, increment=True)

        existing_user_item = Cart.objects.filter(user=user, item_id=item_id,
                                                 wash_category_id=wash_category_id).first()
        if existing_user_item:
            existing_user_item.quantity += quantity
            existing_user_item.price += calculated_price
            existing_user_item.save()
            serializer = self.get_serializer(existing_user_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user, price=calculated_price)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    tags=['Cart'],
)
class CartListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def patch(self, request, *args, **kwargs):
        user = request.user
        item_id = request.data.get('item')
        wash_category_id = request.data.get('wash_category')
        quantity = int(request.data.get('quantity', 1))
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if not wash_category_id:
            wash_category_id = instance.wash_category_id
        if not item_id:
            item_id = instance.item_id

        UserDetailView.update_user_total_price(user, instance.price, increment=False)
        calculated_price = CartListCreateView.calculate_price(item_id, wash_category_id, quantity)
        UserDetailView.update_user_total_price(user, calculated_price, increment=True)

        instance.quantity = quantity
        instance.price = calculated_price
        instance.item_id = item_id
        instance.wash_category_id = wash_category_id
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        UserDetailView.update_user_total_price(user, instance.price, increment=False)
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
