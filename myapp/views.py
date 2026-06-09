from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import UserProfile, Blog

# Create your views here.

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_home')
        return redirect('user_home')

    next_url = request.GET.get('next', '')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        next_url = request.POST.get('next', '')
        if next_url and not next_url.startswith('/'):
            next_url = ''

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if next_url:
                return redirect(next_url)
            if user.is_superuser:
                return redirect('admin_home')
            return redirect('user_home')

        return render(request, 'login.html', {'next': next_url, 'error': 'Invalid username or password'})

    return render(request, 'login.html', {'next': next_url})

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

@login_required
def user_home(request):
    user_profile = UserProfile.objects.filter(USER=request.user).first()
    user_blogs = Blog.objects.filter(USER=request.user).order_by('-created_at')
    stats = {
        'profile': user_profile,
        'blog_count': user_blogs.count(),
        'recent_blogs': user_blogs[:5],
    }
    return render(request, 'user_home.html', stats)

@login_required
@user_passes_test(lambda user: user.is_superuser)
def admin_view(request):
    stats = {
        'user_count': User.objects.count(),
        'profile_count': UserProfile.objects.count(),
        'blog_count': Blog.objects.count(),
        'recent_blogs': Blog.objects.order_by('-created_at')[:5],
    }
    return render(request, 'admin_home.html', stats)


@login_required
def add_blog(request):

   if request.method == "POST":

       title = request.POST['title']
       content = request.POST['content']
       image = request.FILES['image']

       Blog.objects.create(
           USER=request.user,
           title=title,
           content=content,
           image=image
       )

       return redirect('user_home')

   return render(request,'add_blog.html')


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)



