import os
import requests
from django.views import View
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import authenticate, login, logout
from django.core.files.base import ContentFile
from . import forms, models


class LoginView(FormView):

    template_name = "users/login.html"
    form_class = forms.LoginForm
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)


def log_out(request):
    logout(request)
    return redirect(reverse("core:home"))


class SignUpView(FormView):
    template_name = "users/signup.html"
    form_class = forms.SignUpForm
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        form.save()
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
        user.verify_email()
        return super().form_valid(form)


def complete_verification(request, key):
    try:
        user = models.User.objects.get(email_secret=key)
        user.email_verified = True
        user.email_secret = ""
        user.save()
        # TODO: Вывести сообщение об успешной верификации
    except models.User.DoesNotExist:
        # TODO: Добавить сообщение об ошибке
        pass
    return redirect(reverse("core:home"))


def github_login(request):
    client_id = os.environ.get("GH_ID")
    redirect_uri = f"http://localhost:8000/users/login/github/callback"
    return redirect(
        f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=read:user"
    )


class Github_Exception(Exception):
    # TODO Вывести ошибку в интерфейсе
    pass


def github_callback(request):
    try:
        client_id = os.environ.get("GH_ID")
        client_secret = os.environ.get("GH_SECRET")
        code = request.GET.get("code", None)
        if code is not None:
            result = requests.post(
                f"https://github.com/login/oauth/access_token?client_id={client_id}&client_secret={client_secret}&code={code}",
                headers={"Accept": "application/json"},
            )
            result_json = result.json()
            error = result_json.get("error", None)
            if error is not None:
                raise Github_Exception()
            else:
                access_token = result_json.get("access_token")
                profile_request = requests.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/json",
                    },
                )
                profile_json = profile_request.json()
                username = profile_json.get("login", None)
                if username is not None:
                    name = profile_json.get("name")
                    email = profile_json.get("email")
                    bio = profile_json.get("bio")
                    try:
                        user = models.User.objects.get(email=email)
                        if user.login_method != models.User.LOGIN_GITHUB:
                            raise Github_Exception()
                    except models.User.DoesNotExist:
                        user = models.User.objects.create(
                            email=email,
                            first_name=name,
                            username=email,
                            bio=bio,
                            login_method=models.User.LOGIN_GITHUB,
                            email_verified=True,
                        )
                        user.set_unusable_password()
                        user.save()
                    login(request, user)
                    return redirect(reverse("core:home"))
                else:
                    raise Github_Exception()
        else:
            raise Github_Exception()
    except Github_Exception:
        return redirect(reverse("users:login"))


class VK_Exception(Exception):
    # TODO Вывести ошибку в интерфейсе
    pass


def vk_login(request):
    client_id = os.environ.get("VK_APP_ID")
    redirect_uri = f"http://127.0.0.1:8000/users/login/vk/callback"
    return redirect(
        f"https://oauth.vk.com/authorize?client_id={client_id}&display=page&redirect_uri={redirect_uri}&scope=email&response_type=code&v=5.124"
    )


def vk_callback(request):
    try:
        code = request.GET.get("code", None)
        client_id = os.environ.get("VK_APP_ID")
        client_secret = os.environ.get("VK_SECRET")
        redirect_uri = f"http://127.0.0.1:8000/users/login/vk/callback"
        if code is not None:
            token_request = requests.get(
                f"https://oauth.vk.com/access_token?client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}&code={code}"
            )
            token_json = token_request.json()
            error = token_json.get("error", None)
            if error is not None:
                raise VK_Exception()
            access_token = token_json.get("access_token")
            user_id = token_json.get("user_id")
            email = token_json.get("email", None)
            if email is None:
                raise VK_Exception()
            profile_request = requests.get(
                f"https://api.vk.com/method/users.get?user_ids={user_id}&fields=first_name,last_name,photo_max_orig&access_token={access_token}&v=5.89"
            )
            profile_json = profile_request.json()
            response = profile_json.get("response")[0]
            first_name = response.get("first_name")
            last_name = response.get("last_name")
            profile_photo = response.get("photo_max_orig")
            try:
                user = models.User.objects.get(email=email)
                if user.login_method != models.User.LOGIN_VK:
                    raise VK_Exception()
            except models.User.DoesNotExist:
                user = models.User.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    username=email,
                    login_method=models.User.LOGIN_VK,
                    email_verified=True,
                )
                user.set_unusable_password()
                user.save()
                if profile_photo is not None:
                    photo_request = requests.get(profile_photo)
                    user.avatar.save(
                        f"{user_id}-avatar", ContentFile(photo_request.content)
                    )
            login(request, user)
            return redirect(reverse("core:home"))
        else:
            raise VK_Exception()

    except VK_Exception:
        return redirect(reverse("users:login"))
