import uuid

from drf_spectacular.utils import extend_schema
from rest_framework import (
    permissions,
    generics,
    status,
)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from core.api.serializers.key_serializers import (
    ItemSerializer,
    CategorySerializer, UserItemSerializer,
)
from core.custom_view_sets import BaseAttrViewSet
from core.models import (
    Item,
    WashCategory, UserItem,
)
from .user_views import UserDetailView


@extend_schema(
    tags=['Washable Item'],
)
class ItemView(BaseAttrViewSet):
    """Item model views."""
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Item.objects.all()


@extend_schema(
    tags=['Wash Categories'],
)
class CategoryView(BaseAttrViewSet):
    """WashCategory model views."""
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WashCategory.objects.all()


@extend_schema(tags=['User Item'])
class UserItemListCreateView(generics.ListCreateAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = UserItem.objects.all()
    serializer_class = UserItemSerializer
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
        return (UserItemListCreateView.item_price(item_id) +
                UserItemListCreateView.wash_category_price(wash_category_id)) * quantity

    @staticmethod
    def update_user_item(self, item_id, quantity, request, user, wash_category_id) -> Response:
        calculated_price = UserItemListCreateView.calculate_price(item_id, wash_category_id, quantity)
        UserDetailView.update_user_total_price(user, calculated_price, increment=True)
        existing_user_item = UserItem.objects.filter(user=user, item_id=item_id,
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

    def post(self, request, *args, **kwargs):
        user = request.user
        item_id = request.data.get('item')
        wash_category_id = request.data.get('wash_category')
        quantity = int(request.data.get('quantity', 1))

        return UserItemListCreateView.update_user_item(item_id, quantity, request, user, wash_category_id)


@extend_schema(
    tags=['User Item'],
)
class UserItemListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = UserItem.objects.all()
    serializer_class = UserItemSerializer
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

        UserDetailView.update_user_total_price(user, instance.price, increment=False)
        UserItemListCreateView.update_user_item(item_id, quantity, request, user, wash_category_id)
