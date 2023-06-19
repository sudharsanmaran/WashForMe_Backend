from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.api.views.key_views import (
    ItemView, CategoryView, CartListCreateView,
    CartListRetrieveUpdateDestroyView, ShopDetailsView,
    UpdateTimeslots, PickupTimeslotListAPIView, DeliveryTimeslotListAPIView,
    BookingAPIView, BookingListView, PaymentListCreateView, PaymentRetrieveUpdateView,
    OrderListCreateAPIView, OrderRetrieveUpdateDestroyAPIView,
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
    path('cart/', CartListCreateView.as_view(), name='user-item'),
    path('cart/<uuid:id>', CartListRetrieveUpdateDestroyView.as_view(), name='user-item'),
    path('update_timeslots/', UpdateTimeslots.as_view(), name='update-timeslots'),
    path('pickup-timeslots/', PickupTimeslotListAPIView.as_view(), name='pickup-timeslot-list'),
    path('delivery-timeslots/', DeliveryTimeslotListAPIView.as_view(), name='delivery-timeslot-list'),
    path('book-timeslot/', BookingAPIView.as_view(), name='book-timeslot'),
    path('bookings/', BookingListView.as_view(), name='list-bookings'),
    path('payment/', PaymentListCreateView.as_view(), name='payment-list-create'),
    path('payment/<uuid:id>', PaymentRetrieveUpdateView.as_view(), name='payment-retrieve-update-destroy'),
    path('orders/', OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('orders/<uuid:pk>/', OrderRetrieveUpdateDestroyAPIView.as_view(), name='order-retrieve-update-destroy'),
]
