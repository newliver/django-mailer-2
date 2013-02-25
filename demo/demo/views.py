#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.views.generic.base import View
from django_mailer.models import Message
from pyzmail.parse import message_from_string
from django.http import HttpResponse
from mail_utils import get_attachments, get_attachment
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.conf import settings

"""
Shows mail info with attachemnts from django-mailer
Superuser rights are required to acces to the information.
"""


class LoginRequiredMixin(object):
    """
    View mixin which verifies that the user has authenticated.

    NOTE:
    This should be the left-most mixin of a view.

    Code from django_braces
    https://github.com/brack3t/django-braces/blob/master/braces/views.py
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request,
            *args, **kwargs)


class SuperuserRequiredMixin(object):
    """
    Mixin allows you to require a user with `is_superuser` set to True.
    Code from django_braces
    https://github.com/brack3t/django-braces/blob/master/braces/views.py
    """

    login_url = settings.LOGIN_URL  # LOGIN_URL from project settings
    raise_exception = False  # Default whether to raise an exception to none
    redirect_field_name = REDIRECT_FIELD_NAME  # Set by django.contrib.auth

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:  # If the user is a standard user,
            if self.raise_exception:  # *and* if an exception was desired
                raise PermissionDenied  # return a forbidden response.
            else:
                return redirect_to_login(request.get_full_path(),
                                         self.login_url,
                                         self.redirect_field_name)

        return super(SuperuserRequiredMixin, self).dispatch(request,
            *args, **kwargs)




class MailListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    """
    Displays the mail list
    """

    model = Message
    paginate_by = 10

    def get_queryset(self):
        """
        Sort the emails in reverse order
        """
        return super(MailListView, self).get_queryset().order_by('-id')


class MailDetailView(LoginRequiredMixin, SuperuserRequiredMixin, DetailView):
    model = Message

    def get_context_data(self, **kwargs):
        context = super(MailDetailView, self).get_context_data(**kwargs)
        payload_str = self.object.encoded_message.encode('utf-8')
        msg = message_from_string(payload_str)
        context['subject'] = msg.get_subject()
        context['from'] = msg.get_address('from')
        context['to'] = msg.get_addresses('to')
        context['cc'] = msg.get_addresses('cc')
        msg_text = msg.text_part.get_payload() if msg.text_part else None
        msg_html = msg.html_part.get_payload() if msg.html_part else None
        context['msg_html'] = msg_html
        context['msg_text'] = msg_text
        context['attachments'] = get_attachments(msg)
        return context


class MailHtmlDetailView(LoginRequiredMixin, SuperuserRequiredMixin,
                                                            DetailView):
    """
    Shows just the HTML mail for a message, so we can use it to diplay the
    message in an iframe and avoid style classhes with the original
    content.
    """

    model = Message
    template_name = 'django_mailer/html_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MailHtmlDetailView, self).get_context_data(**kwargs)
        payload_str = self.object.encoded_message.encode('utf-8')
        msg = message_from_string(payload_str)
        msg_html = msg.html_part.get_payload() if msg.html_part else None
        context['msg_html'] = msg_html
        return context


class DownloadView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """
    Given a Message and an attachment signature returns the file
    """

    model = Message

    def get_file(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        firma = self.kwargs['firma']
        payload_str = self.model.objects.get(pk=pk).encoded_message.encode('utf-8')
        msg = message_from_string(payload_str)
        return get_attachment(msg, key=firma)

    def get(self, request, *args, **kwargs):
        arx = self.get_file(request, *args, **kwargs)
        response = HttpResponse(mimetype=arx.tipus)
        response['Content-Disposition'] = 'filename=' + arx.filename
        response.write(arx.payload)
        return response
