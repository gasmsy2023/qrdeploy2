from django.contrib import admin
from django.urls import path, include
from certifications.views import home

# change 'Django administration' text
admin.site.site_header = "QR-cert Admin"
admin.site.site_title = "QR-cert Admin"
admin.site.index_title = "Welcome to QR-cert Admin Portal"

urlpatterns = [
    path('', home, name='home'),
    path('admin-dashboard/', admin.site.urls),
    path('certificate/', include('certifications.urls')),
]
