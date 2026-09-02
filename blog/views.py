from django.shortcuts import render
from .models import Blogpost


def index(request):
    myposts = Blogpost.objects.all()
    print(myposts)
    return render(request, 'blog/index.html', {'myposts': myposts})


def blogpost(request, post_id):
    post = Blogpost.objects.get(post_id=post_id)

    return render(request, "blog/blogpost.html", {"post": post})