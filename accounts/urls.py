from django.urls import path
from .views import SignInView, SignOutView, signup, profile

urlpatterns = [
    path('login/', SignInView.as_view(), name='login'),
    path('logout/', SignOutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('profile/', profile, name='profile'),
]
