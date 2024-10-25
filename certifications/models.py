from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid

class Issuer(models.Model):
    name_en = models.CharField('Issuer Name In English', max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    signature = models.ImageField(upload_to='signatures', blank=True)

    def __str__(self):
        return self.name_en

    def get_verify_url(self):
        return settings.BASE_URL + reverse('certifications:verify_issuer', args=[str(self.uuid)])

class CertificateTemplate(models.Model):
    name = models.CharField(max_length=100)
    background_image = models.ImageField(upload_to='certificate_templates', blank=True, null=True)
    font = models.CharField(max_length=50, default='Helvetica')
    title_font_size = models.IntegerField(default=24)
    body_font_size = models.IntegerField(default=18)
    text_color = models.CharField(max_length=7, default='#000000')
    qr_code_position = models.CharField(max_length=20, choices=[
        ('top_left', 'Top Left'),
        ('top_right', 'Top Right'),
        ('bottom_left', 'Bottom Left'),
        ('bottom_right', 'Bottom Right'),
    ], default='bottom_right')

    def __str__(self):
        return self.name

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    noms_et_prenoms = models.CharField('Noms et Prénoms', max_length=100, null=True, blank=True)
    date_de_naissance = models.DateField('Date de Naissance', null=True, blank=True)
    lieu_de_naissance = models.CharField('Lieu de Naissance', max_length=100, null=True, blank=True)
    sexe = models.CharField('Sexe', max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    matricule = models.CharField('Matricule', max_length=50, unique=True, null=True, blank=True)
    mention = models.CharField('Mention', max_length=50, null=True, blank=True)
    session = models.CharField('Session', max_length=50, null=True, blank=True)
    filiere = models.CharField('Filière', max_length=100, null=True, blank=True)
    numero = models.CharField('Numéro', max_length=50, unique=True, null=True, blank=True)
    
    # Keeping important relationships and fields
    issuer = models.ForeignKey(Issuer, on_delete=models.CASCADE)
    issue_date = models.DateTimeField('Date de Délivrance', blank=True, null=True, auto_now_add=True)
    template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    qr_code_link = models.URLField('Lien QR Code', max_length=255, unique=True, blank=True, null=True)

    class Meta:
        unique_together = ['noms_et_prenoms', 'matricule', 'filiere', 'session']

    def __str__(self):
        return f"{self.noms_et_prenoms or ''} | {self.matricule or ''}"

class QRCodeCustomization(models.Model):
    logo = models.ImageField(upload_to='qr_logos', blank=True, null=True)
    foreground_color = models.CharField(max_length=7, default='#000000')
    background_color = models.CharField(max_length=7, default='#FFFFFF')

    def __str__(self):
        return f"QR Code Customization {self.id}"

class SampleCSV(models.Model):
    file = models.FileField(upload_to='sample_csv/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sample CSV {self.id} - {self.created_at}"

class CSVUpload(models.Model):
    file = models.FileField(upload_to='uploads/csv/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    total_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)

    def __str__(self):
        return f"CSV Upload {self.id} - {self.uploaded_at}"

    class Meta:
        ordering = ['-uploaded_at']
