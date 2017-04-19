from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class BackButtonMixin(object):
    def get_back_url(self):
        raise ImproperlyConfigured(
            'You need to overwrite get_back_address to return a URL')

    def get_context_data(self, **kwargs):
        context = super(BackButtonMixin, self).get_context_data(**kwargs)

        context['back_url'] = self.get_back_url

        return context


class AccessMixin(object):
    login_url = None
    raise_exception = False  # Default whether to raise an exception to none
    redirect_field_name = REDIRECT_FIELD_NAME  # Set by django.contrib.auth

    def get_login_url(self):
        return settings.LOGIN_URL

    def get_redirect_field_name(self):
        if self.redirect_field_name is None:
            raise ImproperlyConfigured(
                '{0} is missing the '
                'redirect_field_name. Define {0}.redirect_field_name or '
                'override {0}.get_redirect_field_name().'.format(
                    self.__class__.__name__))
        return self.redirect_field_name


class LoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            if self.raise_exception:
                raise PermissionDenied  # return a forbidden response
            else:
                user_list = User.objects.all()
                if not user_list:
                    return HttpResponseRedirect(reverse('auth_create_admin'))
                else:
                    return redirect_to_login(request.get_full_path(),
                                             self.get_login_url(),
                                             self.get_redirect_field_name())

        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
