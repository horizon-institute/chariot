from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic import CreateView, ListView, UpdateView, DetailView, DeleteView
from django.views.generic.edit import BaseUpdateView

from chariot.mixins import BackButtonMixin, LoginRequiredMixin
from .forms import *
from .models import Deployment

import json


class DeploymentCreateView(LoginRequiredMixin, BackButtonMixin, CreateView):
    form_class = DeploymentCreateForm
    model = Deployment
    template_name = 'deployments/deployment_create.html'

    def get_back_url(self):
        return reverse('home')

    def get_success_url(self):
        return reverse('deployments:update', args=(self.object.id,))


class DeploymentEndView(LoginRequiredMixin, UpdateView):
    form_class = DeploymentEndForm
    model = Deployment

    def get_success_url(self):
        return reverse('deployments:update', args=(self.kwargs['pk'],))


class DeploymentListView(LoginRequiredMixin, ListView):
    context_object_name = 'deployments'
    model = Deployment
    template_name = 'deployments/deployment_list.html'

    def get_context_data(self, **kwargs):
        context = super(DeploymentListView, self).get_context_data(**kwargs)
        context['deployments'] = Deployment.objects.all()
        return context


class DeploymentStartView(LoginRequiredMixin, UpdateView):
    form_class = DeploymentStartForm
    model = Deployment

    def get_success_url(self):
        return reverse('deployments:update', args=(self.kwargs['pk'],))


class DeploymentUpdateView(LoginRequiredMixin, BackButtonMixin, UpdateView):
    template_name = 'deployments/deployment_update.html'
    form_class = DeploymentUpdateForm
    model = Deployment

    def get_back_url(self):
        return reverse('home')

    def get_success_url(self):
        return reverse('deployments:update', args=(self.kwargs['pk'],))


class DeploymentDetailView(LoginRequiredMixin, DetailView):
    model = Deployment
    template_name = 'deployments/deployment_fragment.html'


class DeploymentSensorView(BackButtonMixin, UpdateView):
    model = DeploymentSensor
    template_name = 'deployments/deployment_sensor.html'
    form_class = DeploymentSensorUpdateForm
    context_object_name = 'sensor'

    def get_back_url(self):
        return reverse('deployments:update', args=(self.kwargs.get('pk', None)))

    def get_object(self, queryset=None):
        self.object = DeploymentSensor.objects.get(
            deployment=self.kwargs.get('pk', None),
            sensor=self.kwargs.get('id', None)
        )
        return self.object

    def post(self, request, *args, **kwargs):
        self.object = DeploymentSensor.objects.get(
            deployment=request.POST['deployment'],
            sensor=request.POST['sensor']
        )
        return super(BaseUpdateView, self).post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('deployments:update', args=(self.kwargs.get('pk', None)))


class DeploymentAnnotationCreate(LoginRequiredMixin, CreateView):
    model = DeploymentAnnotation
    form_class = DeploymentAnnotationForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(DeploymentAnnotationCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('deployments:annotation-update', args=(self.object.id,))


class DeploymentAnnotationUpdate(LoginRequiredMixin, UpdateView):
    model = DeploymentAnnotation
    form_class = DeploymentAnnotationForm
    fields = ['start', 'end', 'layer', 'text', 'deployment']

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        annotation = {
            'id': self.object.pk,
            'text': self.object.text,
            'start': self.object.start.strftime("%Y-%m-%d %H:%M:%S"),
            'end': self.object.end.strftime("%Y-%m-%d %H:%M:%S"),
            'layer': self.object.layer,
            'deployment': self.object.deployment.pk
        }
        return HttpResponse(json.dumps(annotation), content_type='application/json')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(DeploymentAnnotationUpdate, self).form_valid(form)

    def form_invalid(self, form):
        form.instance.author = self.request.user
        return super(DeploymentAnnotationUpdate, self).form_invalid(form)

    def get_success_url(self):
        return reverse('deployments:annotation-update', args=(self.kwargs['pk'],))


class DeploymentAnnotationDelete(LoginRequiredMixin, DeleteView):
    model = DeploymentAnnotation
    success_url = 'temp'

    def delete(self, request, *args, **kwargs):
        super(DeploymentAnnotationDelete, self).delete(request, *args, **kwargs)

        return HttpResponse('"success"', content_type='application/json')
