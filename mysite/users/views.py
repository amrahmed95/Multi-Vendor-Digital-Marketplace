from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


from .forms import RegistrationForm, ProfileUpdateForm
from .models import Profile

from vendorhub.models import Vendor

# Create your views here.
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in')
            return redirect('index')
        else:
            messages.error(request, 'Username or password is incorrect')    
            return redirect('users:login')
        
    return render(request, 'users/login.html')

def logout_user(request):
   logout(request)
   messages.success(request, 'You have been logged out')
   return redirect('index')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.is_vendor = form.cleaned_data.get('is_vendor', False)
            profile.save()

            if profile.is_vendor:
                Vendor.objects.create(
                    user=user,
                    business_name=form.cleaned_data['business_name'],
                    contact_email=form.cleaned_data['contact_email'],
                    contact_phone=form.cleaned_data['contact_phone']
                )

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')
            return redirect('users:login')
        else:
            messages.error(request, 'Unsuccessful registration. Please correct the errors below.')
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})
@login_required
def profile(request):
    profile = request.user.profile
    return render(request, 'users/profile.html', {'profile': profile})


@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated')
            return redirect('users:Profile_detail')
        else:
            messages.error(request, 'Unsuccessful profile update. Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/profile_update.html', {'form': form})



class CustomPasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:password_change_done')

class CustomPasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'password_change_done.html'

class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')

class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'