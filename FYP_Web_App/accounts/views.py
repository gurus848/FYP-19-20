#for accounts app
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserDetailsForm
from .models import UserDetails

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def account_info(request):
    obj, _ = UserDetails.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserDetailsForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('account_info')
    else:
        form = UserDetailsForm(instance=obj)
    return render(request, 'account_info.html', {'form': form})