from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the Marketing Automation Home Page")

def about(request):
    return HttpResponse("Welcome to the Marketing Automation About Page")

def services(request):
    return HttpResponse("Welcome to the Marketing Automation Services Page")

def contact(request):
    return HttpResponse("Welcome to the Marketing Automation Contact Page")