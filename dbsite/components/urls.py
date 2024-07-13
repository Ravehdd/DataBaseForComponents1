from django.urls import path, include, re_path
from components.views import *
from dbsite.yasg import urlpatterns as doc_urls
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="Your Project API",
        default_version='v1',
        description="API documentation for Your Project",
        terms_of_service="https://www.yourproject.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourproject.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
)

urlpatterns = [
    path("api/v1/complist/", CompAPIView.as_view(), name="home"),
    path("api/v1/add/", DeviceAPI.as_view(), name="device"),
    path("api/v1/show/", ShowOrderAPI.as_view(), name="show"),
    path("api/v1/replace/", ReplaceAPI.as_view(), name="replace"),
    path("api/v1/update/", UpdateDBAPI.as_view(), name="update"),
    path("api/v1/add-new-device/", AddNewDeviceAPI.as_view(), name="new-device"),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path("api/v1/orders/", OrdersAPIView.as_view(), name="orders"),
    path("api/v1/drf_auth/", include("rest_framework.urls")),
    path("api/v1/auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.authtoken")),#opopooppppo
    # path("api/v1/move/", MoveDataAPI.as_view(), name="move"),
]

# urlpatterns += doc_urls
