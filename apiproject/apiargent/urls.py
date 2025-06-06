from django.urls import path

from . import views

urlpatterns = [
    path('api/', views.AccountView.as_view()),
    path("api/<int:id>/", views.AccountDetailView.as_view()),
    path("api/list/", views.UserAccountsView.as_view()),
]