from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from .forms import ProfileForm


class SignInView(LoginView):
    template_name = 'accounts/login.html'


class SignOutView(LogoutView):
    pass


@login_required
def profile(request):
    profile_obj = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile_obj)
    return render(
        request,
        'accounts/profile.html',
        {'form': form, 'profile_obj': profile_obj},
    )
