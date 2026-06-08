from django.shortcuts import render
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import redirect
from django.contrib.auth.models import User
from .models import UserProfile

# Create your views here.

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:

           login(request, user)

           if user.is_superuser:
               return redirect('/admin')

           else:
               return redirect('/')
    return render(request, 'login.html')

def register(request):
    if request.method == "POST":

       name = request.POST['name']
       email = request.POST['email']
       phone = request.POST['phone']
       place = request.POST['place']
       username = request.POST['username']
       password = request.POST['password']

       user = User.objects.create_user(
           username=username,
           password=password,
           email=email
       )

       UserProfile.objects.create(
           USER=user,
           name=name,
           email=email,
           phone=phone,
           place=place
       )

       return redirect('login')
    return render(request, 'register.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('home')



