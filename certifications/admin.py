from django.contrib import admin
from .models import Issuer, Student, QRCodeCustomization, CertificateTemplate, CSVUpload, SampleCSV

@admin.register(Issuer)
class IssuerAdmin(admin.ModelAdmin):
    list_display = ('name_en',)
    search_fields = ('name_en',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('noms_et_prenoms', 'matricule', 'filiere', 'mention', 'session', 'issuer', 'issue_date')
    list_filter = ('issuer', 'mention', 'session', 'filiere', 'issue_date')
    search_fields = ('noms_et_prenoms', 'matricule', 'numero', 'filiere')
    readonly_fields = ('issue_date',)

@admin.register(QRCodeCustomization)
class QRCodeCustomizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'foreground_color', 'background_color')
    list_filter = ('foreground_color', 'background_color')

@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'qr_code_position')
    list_filter = ('qr_code_position',)
    search_fields = ('name',)

@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

@admin.register(SampleCSV)
class SampleCSVAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'created_at')
    readonly_fields = ('created_at',)
