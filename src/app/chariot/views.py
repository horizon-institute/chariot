from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.template.response import TemplateResponse

import json

from django.views.generic import ListView
from rest_framework.authtoken.models import Token

from chariot.mixins import LoginRequiredMixin, BackButtonMixin
from hubs.models import Hub
from sensors.models import Sensor


def login_view(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')
    else:
        return login(request, template_name='auth/login.html')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ip_view(request):
    obj = {'ip': get_client_ip(request)}
    return HttpResponse(json.dumps(obj), content_type="application/json")


def create_admin_view(request):
    user_list = User.objects.all()
    if not user_list:
        if request.method == "POST":
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            user = User.objects.create_superuser(username, email, password)
            user.first_name = username
            user.save()

            token = Token.objects.create(user=user)
            token.save()

            login(request, user)
            return HttpResponseRedirect('/')
        else:
            return TemplateResponse(request, 'auth/create_admin.html')
    else:
        return HttpResponseRedirect('/')


class DeviceListView(LoginRequiredMixin, BackButtonMixin, ListView):
    model = Sensor
    template_name = 'devices/device_list.html'

    def get_back_url(self):
        return reverse('home')

    def get_context_data(self, **kwargs):
        context = super(DeviceListView, self).get_context_data(**kwargs)
        context['hubs'] = Hub.objects.all()
        return context
