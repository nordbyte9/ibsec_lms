from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import ProfileForm, SignUpForm


class SignInView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class SignOutView(LogoutView):
    next_page = reverse_lazy('login')


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def profile(request):
    profile_obj = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения личного кабинета сохранены.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile_obj)
    return render(
        request,
        'accounts/profile.html',
        {'form': form, 'profile_obj': profile_obj},
    )
