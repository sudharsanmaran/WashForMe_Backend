from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api.views.key_views import (
    ItemView,
    CategoryView, UserItemListCreateView, UserItemListRetrieveUpdateDestroyView, ShopDetailsView,
    SampleCron, PickupTimeslotListAPIView, DeliveryTimeslotListAPIView,
)
from core.api.views.login_views import (
    SendOTPView,
    OTPLoginView,
    DecoratedTokenRefreshView, VerifyOtpView,
)
from core.api.views.user_views import (
    UserDetailView,
    AddressDetailsView,
)

router = DefaultRouter()
router.register('items', ItemView)
router.register('categories', CategoryView)
router.register('address', AddressDetailsView)
router.register('shop', ShopDetailsView)
# router.register('shop_review', ShopReviewView)
app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', DecoratedTokenRefreshView.as_view(), name='token_refresh'),
    path('send_otp/', SendOTPView.as_view(), name='send-otp'),
    path('otp_login/', OTPLoginView.as_view(), name='otp-login'),
    path('verify_otp/', VerifyOtpView.as_view(), name='verify-otp'),
    path('user_details/', UserDetailView.as_view(), name='user-details'),
    path('user_item/', UserItemListCreateView.as_view(), name='user-item'),
    path('user_item/<uuid:id>', UserItemListRetrieveUpdateDestroyView.as_view(), name='user-item'),
    path('cron_test/', SampleCron.as_view(), name='cron-test'),
    path('pickup-timeslots/', PickupTimeslotListAPIView.as_view(), name='pickup-timeslot-list'),
    path('delivery-timeslots/', DeliveryTimeslotListAPIView.as_view(), name='delivery-timeslot-list'),
]
