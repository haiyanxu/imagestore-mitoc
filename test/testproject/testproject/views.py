from django.http import HttpResponse
from django.shortcuts import render

def icons(request):
    return render(request, 'mitocgallery/icons.html')
