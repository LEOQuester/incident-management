from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required

from accounts.forms import LoginForm, RegisterForm, ProfileForm
from accounts.landing import get_post_login_url
from rbac.models import Role


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return get_post_login_url(self.request.user)

    def get_redirect_url(self):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            return get_post_login_url(self.request.user)
        return super().get_redirect_url()


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_post_login_url(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        role = Role.objects.filter(name="Student").first()
        if role:
            self.object.roles.add(role)
        messages.success(
            self.request,
            "Registration successful. Please sign in with your new account.",
        )
        return response


@login_required
def profile(request):
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(
        request,
        "accounts/profile.html",
        {"form": form, "page_title": "My Profile"},
    )
