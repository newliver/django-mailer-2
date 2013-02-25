from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from demo.views import MailListView, MailDetailView, DownloadView
from demo.views import MailHtmlDetailView

urlpatterns = patterns('',
    # Examples:
    url(r'^$', MailListView.as_view(), name='home'),
    url(r'^mail/(?P<pk>\d+)/$', MailDetailView.as_view(),
        name='mail_detail'),
    url('^mail/attachment/(?P<pk>\d+)/(?P<firma>[0-9a-f]{32})/$',
        DownloadView.as_view(),
        name="mail_download"),
    url('^mail/html/(?P<pk>\d+)/$',
        MailHtmlDetailView.as_view(),
        name="mail_html"),
    # Uncomment the next line to enable the admin:
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^admin/', include(admin.site.urls)),
)
