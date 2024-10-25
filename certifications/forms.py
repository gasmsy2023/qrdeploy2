from django import forms
from django.core.exceptions import ValidationError
from .models import CertificateTemplate, Student, Issuer

class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['name', 'background_image', 'qr_code_position']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'noms_et_prenoms', 
            'date_de_naissance', 
            'lieu_de_naissance', 
            'sexe', 
            'matricule', 
            'mention', 
            'session', 
            'filiere', 
            'numero',
            'issuer', 
            'template'
        ]
        widgets = {
            'noms_et_prenoms': forms.TextInput(attrs={'class': 'form-control'}),
            'date_de_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_de_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'mention': forms.TextInput(attrs={'class': 'form-control'}),
            'session': forms.TextInput(attrs={'class': 'form-control'}),
            'filiere': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'issuer': forms.Select(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_matricule(self):
        matricule = self.cleaned_data.get('matricule')
        if Student.objects.filter(matricule=matricule).exists():
            if self.instance and self.instance.matricule == matricule:
                return matricule
            raise ValidationError("Un étudiant avec ce matricule existe déjà.")
        return matricule

    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if Student.objects.filter(numero=numero).exists():
            if self.instance and self.instance.numero == numero:
                return numero
            raise ValidationError("Un étudiant avec ce numéro existe déjà.")
        return numero

    def clean(self):
        cleaned_data = super().clean()
        noms_et_prenoms = cleaned_data.get('noms_et_prenoms')
        matricule = cleaned_data.get('matricule')
        filiere = cleaned_data.get('filiere')
        session = cleaned_data.get('session')

        if noms_et_prenoms and matricule and filiere and session:
            if Student.objects.filter(
                noms_et_prenoms=noms_et_prenoms,
                matricule=matricule,
                filiere=filiere,
                session=session
            ).exists():
                if not (self.instance and self.instance.id):
                    raise ValidationError("Un étudiant avec ces informations existe déjà.")
        return cleaned_data

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='Select a CSV file',
        help_text='Max. 5 megabytes',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'})
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if csv_file:
            if csv_file.size > 5 * 1024 * 1024:  # 5 MB limit
                raise forms.ValidationError("File size must be under 5 MB.")
            if not csv_file.name.endswith('.csv'):
                raise forms.ValidationError("File must be a CSV.")
        return csv_file

class IssuerForm(forms.ModelForm):
    class Meta:
        model = Issuer
        fields = ['name_en', 'signature']
        widgets = {
            'name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'signature': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
