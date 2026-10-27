from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from accounts.views import profile

from accounts.views import RegisterView, UserLoginView, UserLogoutView

app_name = "accounts"

urlpatterns = [
    path("profile/", profile, name="profile"),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="accounts/password_form.html", email_template_name="accounts/password_email.txt", success_url=reverse_lazy("accounts:password_reset_done")), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_form.html", success_url=reverse_lazy("accounts:password_reset_complete")), name="password_reset_confirm"),
    path("reset/complete/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_complete.html"), name="password_reset_complete"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
]
