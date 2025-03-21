from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("accounts/login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path('profile/', views.profile, name='Profile_detail'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', views.CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', views.CustomPasswordResetView.as_view() , name='password_reset'),
    path('password_reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]