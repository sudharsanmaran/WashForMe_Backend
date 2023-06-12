"""
URLS for Core app
"""
from django.urls import path, include


from core.api.views.login_views import (
    CreateOTPView,
    LoginOTPView,
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

router = DefaultRouter()
router.register('items', ItemView)
router.register('categories', CategoryView)
router.register('address', AddressDetailsView)
app_name = 'core'

urlpatterns = [
    path('send_otp/', CreateOTPView.as_view(), name='send-otp'),
    path('check_otp/', LoginOTPView.as_view(), name='check-otp'),
    path('user_details/', UserDetailView.as_view(), name='user-details'),

    path('', include(router.urls)),
]
