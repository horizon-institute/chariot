# encoding:UTF-8

from logging import getLogger
from datetime import datetime  # , timedelta
import re

from django.utils import simplejson as json
from django.contrib.auth.models import User
from django.db.models.fields.files import ImageFieldFile
from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
from django.contrib.sites.models import Site

logger = getLogger('custom')

# these datetime formats are compatible with Javascript
LOCALE_DATE_FMT = "%Y-%m-%d %H:%M:%S"
DATE_FMTS = (LOCALE_DATE_FMT, '%Y-%m-%dT%H:%M:%S.%fZ',
             '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S',
             '%a %b %d %Y %H:%M:%S')


def decode_mac_address(mac_address):
    return mac_address.lower().replace("-", ":")


def to_dict(instance):
    result = {}
    try:
        hidden_fields = instance.hidden_fields
    except:
        hidden_fields = []
    for field in instance._meta.fields:
        name = field.name
        value = getattr(instance, name)
        if name not in hidden_fields and name[0] != '_':
            if issubclass(value.__class__, User):
                result[name] = str(value)
            elif issubclass(value.__class__, models.Model):
                try:
                    result[name] = to_dict(value)
                except:
                    result[name] = value.pk
            elif issubclass(value.__class__, datetime):
                result[name] = value.strftime(LOCALE_DATE_FMT)
            # result[name] = int(mktime(value.timetuple()))
            elif issubclass(value.__class__, ImageFieldFile):
                # get relative URL
                path = value.path
                path = path[path.index('uploads'):]
                path = path.replace('uploads', 'media')
                result[name] = path
            # result[name] = value.get_filename()
            else:
                result[name] = value

    # hack for properties
    try:
        extra_fields = instance.extra_fields
    except:
        extra_fields = []

    for name in extra_fields:
        value = getattr(instance, name)
        if name not in hidden_fields and name[0] != '_':
            if issubclass(value.__class__, User):
                result[name] = str(value)
            # elif issubclass(value.__class__, models.Model):
            #                try:
            #                    result[name] = to_dict(value)
            #                except:
            #                    result[name] = value.pk
            elif issubclass(value.__class__, datetime):
                result[name] = value.strftime(LOCALE_DATE_FMT)
            elif issubclass(value.__class__, ImageFieldFile):
                # get relative URL
                path = value.path
                path = path[path.index('uploads'):]
                path = path.replace('uploads', 'media')
                result[name] = path
            else:
                result[name] = value

    # many-to-many field hack
    for field in instance._meta.many_to_many:
        if field.name not in hidden_fields:
            try:
                result[field.name] = [to_dict(obj) for obj in getattr(instance, field.attname).all()]
            except:
                result[name] = [rel._get_pk_val() for rel in getattr(instance, field.attname).all()]

    return result


def get_json_success(ID):
    return json.dumps({"id": ID})


def get_json_error(reason):
    return json.dumps({"error": {"reason": reason}})


def to_json_list(l):
    result = map(lambda x: x.to_json(), l)
    return '[' + ','.join(result) + ']'


def log_request(view, request):
    user = request.GET.get('user', request.user.id)

    paramsDict = {}
    if request.method == "POST":
        paramsDict = request.POST
    elif request.method == "GET":
        paramsDict = request.GET
    else:
        pass

    params = ', '.join(['"%s": "%s"' % (k, v) for k, v in paramsDict.items()])

    msg = '"user": "%s", "view": "%s", "%s": {%s}' % (user, view, request.method, params)
    logger.info(msg)


def get_requested_user(request):
    user_id = request.GET.get('user_id')
    if user_id in (None, request.user.id):
        return request.user
    else:
        return User.objects.get(id=user_id)


# TODO: fix this function
# decorator function
def can_access_user_data(group_owner, requesting_user, access_type='agent'):
    # passing in user objects
    # logger.debug('requesting user:' + str(requesting_user) +
    #             ', data owner:' + str(group_owner))
    if group_owner is None:
        return True
    if requesting_user.has_perm('sd_store.all_access'):
        return True
    elif group_owner.id == requesting_user.id:
        return True
    groups = []
    for g in requesting_user.groups.all():
        groups.append(str(g.name))
    if group_owner in groups:
        return True
    else:
        return False


# TODO: integrate this in a Django middleware?

firefoxPattern = re.compile('Firefox/(\d+)\.([\d\.-]+)')
chromePattern = re.compile('Chrome/(\d+)\.([\d\.-]+)')
safariPattern = re.compile('Safari/(\d+)\.([\d\.-]+)')
supportedPatterns = (firefoxPattern, chromePattern, safariPattern)


def detect_unsupported_browsers(meta):
    browser = meta['HTTP_USER_AGENT']

    for pattern in supportedPatterns:
        match = pattern.search(browser)
        if match:
            major = int(match.group(1))
            # minor = int(match.group(2))
            if major >= 5:
                return False

    return True


def populate_context(request):
    try:
        experimental_group = not Group.objects.get(name='control') in request.user.groups.all()
    except:
        experimental_group = False
    try:
        unsupported_browser = detect_unsupported_browsers(request.META)
    except KeyError:
        unsupported_browser = False
    context = {
        'ROOT_URL': settings.ROOT_URL,
        'deployment': settings.HOSTING in ('deployment', 'localdeployment'),
        'deployment_local': settings.HOSTING == 'localdeployment',
        'experimental_group': experimental_group,
        'unsupported_browser': unsupported_browser,
        'site': Site.objects.get_current()
    }
    return context
