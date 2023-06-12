"""
URLS for Core app
"""
from django.urls import path, include


from core.api.views.login_views import (
    SendOTPView,
    VerifyOTPView,
)
from core.api.views.key_views import (
    ItemView,
    CategoryView,
)
from core.api.views.user_views import (
    UserDetailView,
    AddressDetailsView,
)

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('items', ItemView)
router.register('categories', CategoryView)
router.register('address', AddressDetailsView)
app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('send_otp/', SendOTPView.as_view(), name='send-otp'),
    path('check_otp/', VerifyOTPView.as_view(), name='check-otp'),
    path('user_details/', UserDetailView.as_view(), name='user-details'),
]
