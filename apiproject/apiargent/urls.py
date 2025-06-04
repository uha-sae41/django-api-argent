from django.urls import path

from . import views

urlpatterns = [
    path('api/', views.AccountView.as_view()),
]