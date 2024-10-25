from django.urls import path
from . import views

app_name = "certifications"

urlpatterns = [
    path('', views.home, name='home'),
    path('index/', views.index, name='index'),
    path('verify/<int:student_id>/', views.verify, name='verify'),
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('download-sample-csv/', views.download_sample_csv, name='download_sample_csv'),
    # path('generate-qr-codes/', views.generate_qr_codes, name='generate_qr_codes'),
    path('download-qr-codes/', views.download_qr_codes, name='download_qr_codes'),
    path('templates/', views.manage_templates, name='manage_templates'),
    path('templates/create/', views.create_template, name='create_template'),
    path('templates/edit/<int:template_id>/', views.edit_template, name='edit_template'),
    path('templates/delete/<int:template_id>/', views.delete_template, name='delete_template'),
    path('student/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('student/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('issuers/', views.list_issuers, name='list_issuers'),
    path('issuers/create/', views.create_issuer, name='create_issuer'),
    path('issuers/edit/<int:issuer_id>/', views.edit_issuer, name='edit_issuer'),
    path('verify-issuer/<uuid:uuid>/', views.verify_issuer, name='verify_issuer'),
    path('student-qr-info/<int:student_id>/', views.student_qr_info, name='student_qr_info'),
]
