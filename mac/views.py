from django.shortcuts import render


# Get an instance of a logger

def index(request):
    return render(request,'index.html')
    

