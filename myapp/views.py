from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q, Count, Exists, OuterRef
from .models import UserProfile, Blog, Follow, BlogLike
from django.urls import reverse

# Create your views here.

def home(request):
    latest_blogs = Blog.objects.order_by('-created_at')[:3]
    return render(request, 'home.html', {'latest_blogs': latest_blogs})

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
    followers_count = Follow.objects.filter(following=request.user).count()
    following_count = Follow.objects.filter(follower=request.user).count()
    stats = {
        'profile': user_profile,
        'blog_count': user_blogs.count(),
        'recent_blogs': user_blogs[:5],
        'followers_count': followers_count,
        'following_count': following_count,
    }
    return render(request, 'user_home.html', stats)

@login_required
@user_passes_test(lambda user: user.is_superuser, login_url='home')
def admin_view(request):
    stats = {
        'user_count': User.objects.count(),
        'profile_count': UserProfile.objects.count(),
        'blog_count': Blog.objects.count(),
        'recent_blogs': Blog.objects.order_by('-created_at')[:5],
        'total_follows': Follow.objects.count(),
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

       if request.user.is_superuser:
           return redirect('admin_home')
       return redirect('user_home')

   return render(request,'add_blog.html')


@login_required
def my_blogs(request):

   blogs = Blog.objects.filter(USER=request.user)

   return render(request,'my_blogs.html',{'blogs':blogs})

@login_required
def blog_feed(request):
    query = request.GET.get('q', '').strip()
    blogs = Blog.objects.all()
    if query:
        blogs = blogs.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(USER__username__icontains=query)
        )
    # annotate like counts
    blogs = blogs.annotate(like_count=Count('likes'))
    # annotate whether current user liked each blog
    if request.user.is_authenticated:
        user_likes = BlogLike.objects.filter(blog=OuterRef('pk'), user=request.user)
        blogs = blogs.annotate(user_liked=Exists(user_likes))
    else:
        blogs = blogs.annotate(user_liked=Exists(BlogLike.objects.none()))

    blogs = blogs.order_by('-created_at')
    return render(request, 'blog_feed.html', {'blogs': blogs, 'query': query})

@login_required
def edit_blog(request,id):

   blog = Blog.objects.get(id=id)

   if request.method == "POST":

       blog.title = request.POST['title']
       blog.content = request.POST['content']

       if 'image' in request.FILES:
           blog.image = request.FILES['image']

       blog.save()

       return redirect('my_blogs')

   return render(request,'edit_blog.html',{'blog':blog})

@login_required
def delete_blog(request,id):

   blog = Blog.objects.get(id=id)

   blog.delete()

   return redirect('my_blogs')

@login_required
@user_passes_test(lambda user: user.is_superuser, login_url='home')
def delete_blog_admin(request,id):

   blog = Blog.objects.get(id=id)

   blog.delete()

   return redirect('view_blogs_admin')


def profile(request, username):
    """Display a user's profile and their blogs"""
    user = get_object_or_404(User, username=username)
    
    # Do not allow non-admin users to view an admin profile.
    if user.is_superuser and not request.user.is_superuser:
        return redirect('home')

    user_profile = get_object_or_404(UserProfile, USER=user)
    user_blogs = Blog.objects.filter(USER=user).order_by('-created_at')
    
    is_own_profile = request.user == user
    
    # Get follower and following counts
    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    
    # Check if current user is following this user
    is_following = False
    if request.user.is_authenticated and not is_own_profile:
        is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    
    context = {
        'profile_user': user,
        'user_profile': user_profile,
        'user_blogs': user_blogs,
        'blog_count': user_blogs.count(),
        'is_own_profile': is_own_profile,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    }
    
    return render(request, 'profile.html', context)


@login_required
def follow_user(request, username):
    """Follow a user"""
    user_to_follow = get_object_or_404(User, username=username)
    
    # Can't follow yourself
    if request.user == user_to_follow:
        return redirect('profile', username=username)
    
    # Create follow relationship
    Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    return redirect('profile', username=username)


@login_required
def unfollow_user(request, username):
    """Unfollow a user"""
    user_to_unfollow = get_object_or_404(User, username=username)
    
    # Can't unfollow yourself
    if request.user == user_to_unfollow:
        return redirect('profile', username=username)
    
    # Delete follow relationship
    Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()
    
    return redirect('profile', username=username)


@login_required
def followers_list(request, username):
    """Display list of followers for a user"""
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    is_own_profile = request.user == user
    
    context = {
        'profile_user': user,
        'followers': [follow.follower for follow in followers],
        'is_own_profile': is_own_profile,
        'followers_count': followers.count(),
    }
    
    return render(request, 'followers_list.html', context)


@login_required
def following_list(request, username):
    """Display list of users that a user is following"""
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')
    
    is_own_profile = request.user == user
    
    context = {
        'profile_user': user,
        'following': [follow.following for follow in following],
        'is_own_profile': is_own_profile,
        'following_count': following.count(),
    }
    
    return render(request, 'following_list.html', context)


@login_required
def remove_follower(request, username):
    """Remove a follower"""
    follower_user = get_object_or_404(User, username=username)
    
    # Only owner can remove followers
    Follow.objects.filter(
        follower=follower_user,
        following=request.user
    ).delete()
    
    return redirect('followers_list', username=request.user.username)


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

@login_required
@user_passes_test(lambda user: user.is_superuser, login_url='home')
def view_blogs_admin(request):

   blogs = Blog.objects.all()

   return render(request,'view_blogs_admin.html',{'blogs':blogs})

@login_required
@user_passes_test(lambda user: user.is_superuser, login_url='home')
def view_users(request):

   users = UserProfile.objects.all()

   return render(request,'view_users.html',{'users':users})


def blog_detail(request, id):
    """Show a single blog post detail."""
    blog = get_object_or_404(Blog, id=id)
    author_profile = UserProfile.objects.filter(USER=blog.USER).first()
    # like info
    like_count = BlogLike.objects.filter(blog=blog).count()
    is_liked = False
    if request.user.is_authenticated:
        is_liked = BlogLike.objects.filter(blog=blog, user=request.user).exists()

    context = {
        'blog': blog,
        'author_profile': author_profile,
        'like_count': like_count,
        'is_liked': is_liked,
    }
    return render(request, 'blog_detail.html', context)


@login_required
def like_blog(request, id):
    # Accept only POST for creating a like; after action, return to referrer when possible
    if request.method != 'POST':
        ref = request.META.get('HTTP_REFERER')
        if ref:
            return redirect(ref)
        return redirect('blog_detail', id=id)
    blog = get_object_or_404(Blog, id=id)
    if request.user == blog.USER:
        ref = request.META.get('HTTP_REFERER')
        if ref:
            return redirect(ref)
        return redirect('blog_detail', id=id)
    BlogLike.objects.get_or_create(user=request.user, blog=blog)
    ref = request.META.get('HTTP_REFERER')
    if ref:
        return redirect(ref)
    return redirect('blog_detail', id=id)


@login_required
def unlike_blog(request, id):
    # Accept only POST for removing a like; return to referring page when possible
    if request.method != 'POST':
        ref = request.META.get('HTTP_REFERER')
        if ref:
            return redirect(ref)
        return redirect('blog_detail', id=id)
    blog = get_object_or_404(Blog, id=id)
    BlogLike.objects.filter(user=request.user, blog=blog).delete()
    ref = request.META.get('HTTP_REFERER')
    if ref:
        return redirect(ref)
    return redirect('blog_detail', id=id)



