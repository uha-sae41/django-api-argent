from django.urls import path

from . import views

urlpatterns = [
    path('api/', views.AccountView.as_view()),
    path("api/<int:id>/", views.AccountDetailView.as_view()),
    path("api/list/", views.UserAccountsView.as_view()),
    path("api/list/<int:id>/", views.UserAccountsViewById.as_view()),
    path("api/<int:id>/balance/update/", views.AccountBalanceUpdateView.as_view()),
    path("api/<int:id>/logs/", views.AccountLogView.as_view()),
    path("api/<int:id>/logs/<int:nombre>/", views.AccountLogView.as_view()),
    path("api/<int:id>/virement/", views.AccountVirementView.as_view()),
    path("api/pending-actions/", views.PendingActionsView.as_view()),
    path("api/validate-action/<int:id>/", views.ValidateActionView.as_view()),
    path("api/decline-action/<int:id>/", views.DeclineActionView.as_view()),
    path("api/change-account-state/<int:id>/", views.ChangeAccountStateView.as_view()),
    path("api/list-process-created-accounts/", views.ListCreatedProcessAccountsView.as_view()),
    path("api/request-new-account/", views.RequestNewAccountView.as_view()),
]