from __future__ import absolute_import

"""
- ``validate_signed_request``: Function decorator. Validate request signature. Applies appropriate validation
  mechanism to the request data. Assumes ``SKA_SECRET_KEY`` to be in ``settings`` module.

  Arguments to be used with `ska.validate_signed_request_data` shortcut function.

  :param str secret_key: The shared secret key.
  :param str signature_param: Name of the (for example GET or POST) param name which holds
      the ``signature`` value.
  :param str auth_user_param: Name of the (for example GET or POST) param name which holds
      the ``auth_user`` value.
  :param str valid_until_param: Name of the (foe example GET or POST) param name which holds
      the ``valid_until`` value.

- ``sign_url``: Method decorator (to be used in models). Signs the URL.

  Arguments to be used with `ska.sign_url` shortcut function.

  :param str auth_user: Username of the user making the request.
  :param str secret_key: The shared secret key.
  :param float|str valid_until: Unix timestamp. If not given, generated automatically (now + lifetime).
  :param int lifetime: Signature lifetime in seconds.
  :param str suffix: Suffix to add after the ``endpoint_url`` and before the appended signature params.
  :param str signature_param: Name of the GET param name which would hold the generated signature value.
  :param str auth_user_param: Name of the GET param name which would hold the ``auth_user`` value.
  :param str valid_until_param: Name of the GET param name which would hold the ``valid_until`` value.
"""

__title__ = 'ska.contrib.django.ska.decorators'
__author__ = 'Artur Barseghyan'
__copyright__ = 'Copyright (c) 2013 Artur Barseghyan'
__license__ = 'GPL 2.0/LGPL 2.1'
__all__ = ('validate_signed_request', 'sign_url')

from six import PY3, text_type

from ska import validate_signed_request_data, sign_url as ska_sign_url
from ska.defaults import (
    SIGNATURE_LIFETIME, DEFAULT_URL_SUFFIX, DEFAULT_SIGNATURE_PARAM, DEFAULT_AUTH_USER_PARAM,
    DEFAULT_VALID_UNTIL_PARAM, DEFAULT_EXTRA_PARAM
    )
from ska.contrib.django.ska.settings import (
    SECRET_KEY, AUTH_USER, UNAUTHORISED_REQUEST_ERROR_MESSAGE,
    UNAUTHORISED_REQUEST_ERROR_TEMPLATE
    )
from ska.contrib.django.ska.http import HttpResponseUnauthorized

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render

class BaseValidateSignedRequest(object):
    def __init__(self, secret_key=SECRET_KEY, signature_param=DEFAULT_SIGNATURE_PARAM, \
                 auth_user_param=DEFAULT_AUTH_USER_PARAM, valid_until_param=DEFAULT_VALID_UNTIL_PARAM, \
                 extra_param=DEFAULT_EXTRA_PARAM):
        self.secret_key = secret_key
        self.signature_param = signature_param
        self.auth_user_param = auth_user_param
        self.valid_until_param = valid_until_param
        self.extra_param = extra_param

class ValidateSignedRequest(BaseValidateSignedRequest):
    """
    Function decorator. Validate request signature. Applies appropriate validation mechanism to the request
    data. Assumes ``SKA_SECRET_KEY`` to be in ``settings`` module.

    Arguments to be used with `ska.validate_signed_request_data` shortcut function.

    :attribute str secret_key: The shared secret key.
    :attribute str signature_param: Name of the (for example GET or POST) param name which holds
        the ``signature`` value.
    :attribute str auth_user_param: Name of the (for example GET or POST) param name which holds
        the ``auth_user`` value.
    :attribute str valid_until_param: Name of the (foe example GET or POST) param name which holds
        the ``valid_until`` value.
    :attribute str extra_param: Name of the (foe example GET or POST) param name which holds
        the ``extra`` value.

    :example:

    >>> from ska.contrib.django.ska.decorators import validate_signed_request
    >>> 
    >>> @validate_signed_request()
    >>> def detail(request, slug, template_name='foo/detail.html'):
    >>>     # Your code
    """
    def __call__(self, func):
        def inner(request, *args, **kwargs):
            # Validating the request.
            validation_result = validate_signed_request_data(
                data = request.REQUEST,
                secret_key = self.secret_key,
                signature_param = self.signature_param,
                auth_user_param = self.auth_user_param,
                valid_until_param = self.valid_until_param,
                extra_param = self.extra_param
                )
            if validation_result.result is True:
                # If validated, just return the func as is.
                return func(request, *args, **kwargs)
            else:
                # Otherwise...
                if UNAUTHORISED_REQUEST_ERROR_TEMPLATE:
                    # If template to display the error message is set in ska (django-ska) settings,
                    # use it to render the message and return ``HttpResponseUnauthorized`` response
                    # describing the error.
                    response_content = render(
                        request,
                        UNAUTHORISED_REQUEST_ERROR_TEMPLATE,
                        {'reason': '; '.join(validation_result.reason)}
                        )
                    return HttpResponseUnauthorized(response_content)
                else:
                    # Otherwise, return plain text message with describing the error.
                    return HttpResponseUnauthorized(
                        _(UNAUTHORISED_REQUEST_ERROR_MESSAGE).format('; '.join(validation_result.reason))
                        )
        return inner

validate_signed_request = ValidateSignedRequest


class MethodValidateSignedRequest(BaseValidateSignedRequest):
    """
    Method decorator. Validate request signature. Applies appropriate validation mechanism to the request
    data. Assumes ``SKA_SECRET_KEY`` to be in ``settings`` module.

    Arguments to be used with `ska.validate_signed_request_data` shortcut function.

    :attribute str secret_key: The shared secret key.
    :attribute str signature_param: Name of the (for example GET or POST) param name which holds
        the ``signature`` value.
    :attribute str auth_user_param: Name of the (for example GET or POST) param name which holds
        the ``auth_user`` value.
    :attribute str valid_until_param: Name of the (foe example GET or POST) param name which holds
        the ``valid_until`` value.
    :attribute str extra_param: Name of the (foe example GET or POST) param name which holds
        the ``extra`` value.

    :example:

    >>> from ska.contrib.django.ska.decorators import m_validate_signed_request
    >>> 
    >>> class FooDetailView(View):
    >>>     @validate_signed_request()
    >>>     def get(self, request, slug, template_name='foo/detail.html'):
    >>>         # Your code
    """
    def __call__(self, func):
        def inner(this, request, *args, **kwargs):
            # Validating the request.
            validation_result = validate_signed_request_data(
                data = request.REQUEST,
                secret_key = self.secret_key,
                signature_param = self.signature_param,
                auth_user_param = self.auth_user_param,
                valid_until_param = self.valid_until_param,
                extra_param = self.extra_param
                )
            if validation_result.result is True:
                # If validated, just return the func as is.
                return func(this, request, *args, **kwargs)
            else:
                # Otherwise...
                if UNAUTHORISED_REQUEST_ERROR_TEMPLATE:
                    # If template to display the error message is set in ska (django-ska) settings,
                    # use it to render the message and return ``HttpResponseUnauthorized`` response
                    # describing the error.
                    response_content = render(
                        request,
                        UNAUTHORISED_REQUEST_ERROR_TEMPLATE,
                        {'reason': '; '.join(validation_result.reason)}
                        )
                    return HttpResponseUnauthorized(response_content)
                else:
                    # Otherwise, return plain text message with describing the error.
                    return HttpResponseUnauthorized(
                        _(UNAUTHORISED_REQUEST_ERROR_MESSAGE).format('; '.join(validation_result.reason))
                        )
        return inner

m_validate_signed_request = MethodValidateSignedRequest


class SignAbsoluteURL(object):
    """
    Method decorator (to be used in models). Signs the URL.

    Arguments to be used with `ska.sign_url` shortcut function.

    :attribute str auth_user: Username of the user making the request.
    :attribute str secret_key: The shared secret key.
    :attribute float|str valid_until: Unix timestamp. If not given, generated automatically (now + lifetime).
    :attribute int lifetime: Signature lifetime in seconds.
    :attribute str suffix: Suffix to add after the ``endpoint_url`` and before the appended signature params.
    :attribute str signature_param: Name of the GET param name which would hold the generated signature value.
    :attribute str auth_user_param: Name of the GET param name which would hold the ``auth_user`` value.
    :attribute str valid_until_param: Name of the GET param name which would hold the ``valid_until`` value.
    :attribute dict extra: Dict of extra params to append to signed URL.
    :attribute str extra_param: Name of the GET param name which would hold the ``extra`` value.

    :example:

    >>> from ska.contrib.django.ska.decorators import sign_url
    >>> 
    >>> class FooItem(models.Model):
    >>>     title = models.CharField(_("Title"), max_length=100)
    >>>     slug = models.SlugField(unique=True, verbose_name=_("Slug"))
    >>>     body = models.TextField(_("Body"))
    >>>
    >>>     @sign_url()
    >>>     def get_signed_absolute_url(self):
    >>>         return reverse('foo.detail', kwargs={'slug': self.slug})
    """
    def __init__(self, auth_user=AUTH_USER, secret_key=SECRET_KEY, valid_until=None, lifetime=SIGNATURE_LIFETIME, \
                 suffix=DEFAULT_URL_SUFFIX, signature_param=DEFAULT_SIGNATURE_PARAM, \
                 auth_user_param=DEFAULT_AUTH_USER_PARAM, valid_until_param=DEFAULT_VALID_UNTIL_PARAM, \
                 extra={}, extra_param=DEFAULT_EXTRA_PARAM):
        self.auth_user = auth_user
        self.secret_key = secret_key
        self.valid_until = valid_until
        self.lifetime = lifetime
        self.suffix = suffix
        self.signature_param = signature_param
        self.auth_user_param = auth_user_param
        self.valid_until_param = valid_until_param
        self.extra = extra
        self.extra_param = extra_param

    def __call__(self, func):
        def inner(this, *args, **kwargs):
            if not PY3:
                url = text_type(func(this, *args, **kwargs))
            else:
                url = func(this, *args, **kwargs)

            return ska_sign_url(
                auth_user = self.auth_user,
                secret_key = self.secret_key,
                valid_until = self.valid_until,
                lifetime = self.lifetime,
                url = url,
                suffix = self.suffix,
                signature_param = self.signature_param,
                auth_user_param = self.auth_user_param,
                valid_until_param = self.valid_until_param,
                extra = self.extra,
                extra_param = self.extra_param
                )
        return inner

sign_url = SignAbsoluteURL
