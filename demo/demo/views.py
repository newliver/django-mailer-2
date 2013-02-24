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


class MailListView(ListView):
    model = Message
    paginate_by = 10

class MailDetailView(DetailView):
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


class DownloadView(View):
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
