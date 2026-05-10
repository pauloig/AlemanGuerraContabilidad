from django.shortcuts import render, redirect
from django.http import HttpResponse
from datetime import datetime
from django.contrib.auth import authenticate, login as login_process
from django.contrib.auth.decorators import login_required
from . import views
from django.contrib.auth.models import User

@login_required(login_url='/login/')
def home(request):
 #       return HttpResponse("Bienvenido")
      return render(
        request,
        'index.html',
        {
            'title':'Home Page',
           'year':datetime.now().year,
        }
    )

def login(request):
    state = 0
    message = ""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login_process(request, user)
            state = 1
            message = ""
            return redirect('/home/')
        else:
            state = 2
            message = "Username or password is incorrect"
    dic = {'state': state, 'message': message}
    return render(request, 'login.html', dic)


@login_required
def user_list(request):
    users = User.objects.all()
    context = {
        'users': users,
        'app_selected': 7,  # Para marcar "Usuarios" como activo en el menú
    }
    return render(request, 'user_list.html', context)