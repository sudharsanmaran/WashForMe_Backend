import uuid
from datetime import datetime

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import (
    permissions,
    generics,
    status,
)
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from core.api.serializers.key_serializers import (
    ItemSerializer,
    CategorySerializer, UserItemSerializer, ShopSerializer, TimeslotSerializer,
)
from core.custom_view_sets import BaseAttrViewSet
from core.models import (
    Item,
    WashCategory, UserItem, Shop, Timeslot,
)
from .user_views import UserDetailView
from ...cron import update_timeslots


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

    def post(self, request, *args, **kwargs):
        user = request.user
        item_id = request.data.get('item')
        wash_category_id = request.data.get('wash_category')
        quantity = int(request.data.get('quantity', 1))

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

        if not wash_category_id:
            wash_category_id = instance.wash_category_id
        if not item_id:
            item_id = instance.item_id

        UserDetailView.update_user_total_price(user, instance.price, increment=False)
        calculated_price = UserItemListCreateView.calculate_price(item_id, wash_category_id, quantity)
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


@extend_schema(
    tags=['Shop Details'],
)
class ShopDetailsView(BaseAttrViewSet):
    """AddressDetails model views."""
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Shop.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# @extend_schema(
#     tags=['Shop Review'],
# )
# class ShopReviewView(BaseAttrViewSet):
#     """AddressDetails model views."""
#     serializer_class = ShopReviewSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     queryset = Review.objects.all()
#
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)


class SampleCron(APIView):
    def get(self, request, *args, **kwargs):
        update_timeslots()
        return Response(status=status.HTTP_200_OK)


@extend_schema(
    tags=['Timeslots'],
    parameters=[
        OpenApiParameter(name='start_datetime', type=str),
        OpenApiParameter(name='end_datetime', type=str),
    ]
)
class TimeslotListAPIView(generics.ListAPIView):
    serializer_class = TimeslotSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        try:
            start_datetime = datetime.strptime(self.request.query_params.get('start_datetime'), '%Y-%m-%d')
            end_datetime = datetime.strptime(self.request.query_params.get('end_datetime'), '%Y-%m-%d')
        except Exception as e:
            raise ValidationError('parameters must be in date format like \'2023-12-24\'')

        queryset = Timeslot.objects.all()

        if start_datetime:
            queryset = queryset.filter(start_datetime__gte=start_datetime)
        if end_datetime:
            queryset = queryset.filter(end_datetime__lte=end_datetime)

        return queryset
