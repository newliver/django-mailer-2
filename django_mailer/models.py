#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

from django.db import models
from django_mailer import constants, managers
import datetime


PRIORITIES = (
    (constants.PRIORITY_HIGH, 'high'),
    (constants.PRIORITY_NORMAL, 'normal'),
    (constants.PRIORITY_LOW, 'low'),
)

RESULT_CODES = (
    (constants.RESULT_SENT, 'success'),
    (constants.RESULT_SKIPPED, 'not sent (blacklisted)'),
    (constants.RESULT_FAILED, 'failure'),
)


class Message(models.Model):
    """
    An email message.

    The ``to_address``, ``from_address`` and ``subject`` fields are merely for
    easy of access for these common values. The ``encoded_message`` field
    contains the entire encoded email message ready to be sent to an SMTP
    connection.

    """
    to_address = models.CharField(max_length=200)
    from_address = models.CharField(max_length=200)
    subject = models.CharField(max_length=255)

    encoded_message = models.TextField()
    date_created = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = ('date_created',)

    def __unicode__(self):
        return '%s: %s' % (self.to_address, self.subject)


class QueuedMessage(models.Model):
    """
    A queued message.

    Messages in the queue can be prioritised so that the higher priority
    messages are sent first (secondarily sorted by the oldest message).

    """
    message = models.OneToOneField(Message, editable=False)
    priority = models.PositiveSmallIntegerField(choices=PRIORITIES,
                                            default=constants.PRIORITY_NORMAL)
    deferred = models.DateTimeField(null=True, blank=True)
    retries = models.PositiveIntegerField(default=0)
    date_queued = models.DateTimeField(default=datetime.datetime.now)

    objects = managers.QueueManager()

    class Meta:
        ordering = ('priority', 'date_queued')

    def defer(self):
        self.deferred = datetime.datetime.now()
        self.save()


class Blacklist(models.Model):
    """
    A blacklisted email address.

    Messages attempted to be sent to e-mail addresses which appear on this
    blacklist will be skipped entirely.

    """
    email = models.EmailField(max_length=200)
    date_added = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = ('-date_added',)
        verbose_name = 'blacklisted e-mail address'
        verbose_name_plural = 'blacklisted e-mail addresses'


class Log(models.Model):
    """
    A log used to record the activity of a queued message.

    """
    message = models.ForeignKey(Message, editable=False)
    result = models.PositiveSmallIntegerField(choices=RESULT_CODES)
    date = models.DateTimeField(default=datetime.datetime.now)
    log_message = models.TextField()

    class Meta:
        ordering = ('-date',)


class EmailManager(models.Manager):

    def get_available_email(self):
        enabled_email = self.get_query_set().filter(enabled=1)
        today = datetime.date.today()
        for email in enabled_email:
            msg = Message.objects.filter(from_address__contains=email.host_user,
                                         date_created__contains=today)
            if email.block_size > msg.count():
                return email


class Email(models.Model):

    """
    Multi email account support.
    """

    host_user = models.EmailField(max_length=200)
    host_password = models.CharField(max_length=32)
    default_from_email = models.EmailField(max_length=200)
    email_host = models.CharField(max_length=200,
                                  default='smtp.gmail.com')
    email_port = models.IntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    block_size = models.IntegerField(default=500)
    enabled = models.SmallIntegerField(default=1)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(null=True, blank=True, auto_now=True)
    objects = EmailManager()

    def send_count_today(self):
        today = datetime.date.today()
        send_count = Message.objects.filter(from_address__contains=self.host_user,
                                            date_created__contains=today).count()
        return send_count

    class Meta:
        ordering = ('date_updated',)
        unique_together = ('host_user',)

    def __unicode__(self):
        return '%s' % self.host_user
