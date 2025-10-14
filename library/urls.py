
from django.urls import path, include
from rest_framework import routers
from library import views

router = routers.DefaultRouter()
router.register(r'authors', views.AuthorViewSet)
router.register(r'books', views.BookViewSet)
router.register(r'members', views.MemberViewSet)
router.register(r'loans', views.LoanViewSet)

app_name = 'api'

urlpatterns = [
    path('api/', include(router.urls)),
]