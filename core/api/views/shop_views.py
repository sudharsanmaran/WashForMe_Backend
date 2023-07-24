from drf_spectacular.utils import extend_schema
from rest_framework import permissions

from core.api.serializers.shop_serializers import ShopSerializer
from core.custom_view_sets import BaseAttrViewSet
from core.models import Shop
from core.signals import create_shop_timeslots_signal, delete_shop_timeslots_signal


@extend_schema(
    tags=['Shop Details'],
)
class ShopDetailsView(BaseAttrViewSet):
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Shop.objects.all()

    def perform_create(self, serializer):
        shop = serializer.save(user=self.request.user)
        create_shop_timeslots_signal.send(sender=self.__class__, shop=shop)

    def perform_update(self, serializer):
        shop_before_update = self.get_object()
        serialized_data_before_update = serializer.to_representation(shop_before_update)

        shop = serializer.save()

        serialized_data_after_update = serializer.data

        fields_to_check = ['active', 'opening_time', 'closing_time', 'wash_duration', 'time_slot_duration',
                           'max_user_limit_per_time_slot']

        if any(serialized_data_before_update[field] != serialized_data_after_update[field] for field in
               fields_to_check):
            delete_shop_timeslots_signal.send(sender=self.__class__, shop=shop)
            if shop.active:
                create_shop_timeslots_signal.send(sender=self.__class__, shop=shop)

    def perform_destroy(self, instance):
        delete_shop_timeslots_signal.send(sender=self.__class__, shop=instance)
        instance.delete()

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
