import io
import csv
import qrcode
import zipfile
import os
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files.storage import default_storage
from django.urls import reverse
from certifications.models import Student, QRCodeCustomization, Issuer, CertificateTemplate, CSVUpload, SampleCSV
from certifications.forms import CertificateTemplateForm, IssuerForm, StudentForm, CSVUploadForm
from PIL import Image

def home(request):
    return render(request, 'home.html')

def index(request):
    students_list = Student.objects.all().order_by('-id')  # Order by most recently added
    paginator = Paginator(students_list, 10)  # Show 10 students per page

    page = request.GET.get('page')
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        students = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        students = paginator.page(paginator.num_pages)

    return render(request, 'index.html', {'students': students})

def regenerate_all_qr_codes(request):
    """View to regenerate QR codes for all students"""
    students = Student.objects.all()
    count = 0
    for student in students:
        qr_code_url = generate_qr_code(student.id)
        student.qr_code_link = qr_code_url
        student.save()
        count += 1
    
    messages.success(request, f'Successfully regenerated QR codes for {count} students.')
    return redirect('certifications:index')

def download_sample_csv(request):
    # Create a new CSV file in memory
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_students.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['noms_et_prenoms', 'matricule', 'filiere', 'mention', 'session', 'sexe', 'date_de_naissance', 'lieu_de_naissance', 'numero', 'issuer_name_en'])
    
    # Add a sample row
    writer.writerow(['John Doe', '12345', 'Computer Science', 'Très Bien', '2024', 'M', '2000-01-01', 'Paris', 'CERT001', 'University of Example'])
    
    return response

def generate_qr_code(student_id):
    """Generate a single QR code for a student"""
    qr_customization = QRCodeCustomization.objects.first()
    if not qr_customization:
        qr_customization = QRCodeCustomization.objects.create()

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Get the relative URL using reverse
    relative_url = reverse('certifications:student_qr_info', args=[student_id])
    # Combine BASE_URL with 'certificate' prefix and the relative URL
    student_url = f"{settings.BASE_URL.rstrip('/')}{relative_url}"
    qr.add_data(student_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color=qr_customization.foreground_color, back_color=qr_customization.background_color)

    if qr_customization.logo:
        logo = Image.open(qr_customization.logo.path)
        logo_size = (qr_img.size[0] // 4, qr_img.size[1] // 4)
        logo = logo.resize(logo_size, Image.LANCZOS)
        pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
        qr_img.paste(logo, pos, logo)

    # Save QR code image to media storage
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    qr_code_path = f'qr_codes/student_{student_id}.png'
    default_storage.save(qr_code_path, ContentFile(qr_buffer.getvalue()))
    
    # Return the full URL for the QR code
    return f"{settings.BASE_URL}{settings.MEDIA_URL}{qr_code_path}"

def convert_date_format(date_str):
    """Convert date from DD/MM/YYYY to YYYY-MM-DD format"""
    if not date_str:
        return None
    try:
        # Parse the date string in DD/MM/YYYY format
        date_obj = datetime.strptime(date_str.strip(), '%d/%m/%Y')
        # Convert to YYYY-MM-DD format
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Try parsing as YYYY-MM-DD in case it's already in the correct format
            datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return date_str.strip()
        except ValueError:
            return None

def upload_csv(request):
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Please select a CSV file to upload.')
            return redirect('certifications:upload_csv')

        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File must be a CSV.')
            return redirect('certifications:upload_csv')

        try:
            # Try different encodings
            encodings = ['utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            decoded_file = None
            
            for encoding in encodings:
                try:
                    csv_file.seek(0)  # Reset file pointer
                    decoded_file = csv_file.read().decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if decoded_file is None:
                messages.error(request, 'Unable to decode CSV file. Please ensure it is properly encoded.')
                return redirect('certifications:upload_csv')

            csv_data = csv.DictReader(io.StringIO(decoded_file))
            
            success_count = 0
            error_count = 0
            skip_count = 0
            error_messages = []

            with transaction.atomic():
                for row in csv_data:
                    try:
                        # Check if student with this matricule already exists
                        matricule = row.get('matricule', '').strip()
                        if not matricule:
                            error_count += 1
                            error_messages.append(f"Error in row {success_count + error_count + skip_count}: Missing matricule")
                            continue

                        if Student.objects.filter(matricule=matricule).exists():
                            skip_count += 1
                            continue

                        # Get or create issuer
                        issuer_name = row.get('issuer_name_en', '').strip()
                        if not issuer_name:
                            error_count += 1
                            error_messages.append(f"Error in row {success_count + error_count + skip_count}: Missing issuer name")
                            continue

                        issuer, _ = Issuer.objects.get_or_create(
                            name_en=issuer_name
                        )

                        # Convert date format
                        date_de_naissance = convert_date_format(row.get('date_de_naissance', '').strip())

                        # Create student record
                        student = Student.objects.create(
                            noms_et_prenoms=row.get('noms_et_prenoms', '').strip(),
                            matricule=matricule,
                            filiere=row.get('filiere', '').strip(),
                            mention=row.get('mention', '').strip(),
                            session=row.get('session', '').strip(),
                            sexe=row.get('sexe', '').strip(),
                            date_de_naissance=date_de_naissance,
                            lieu_de_naissance=row.get('lieu_de_naissance', '').strip(),
                            numero=row.get('numero', '').strip(),
                            issuer=issuer
                        )
                        
                        # Generate QR code for the student
                        qr_code_url = generate_qr_code(student.id)
                        student.qr_code_link = qr_code_url
                        student.save()
                        
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Error in row {success_count + error_count + skip_count}: {str(e)}")
                        continue

            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} student records.')
            if skip_count > 0:
                messages.info(request, f'Skipped {skip_count} duplicate records.')
            if error_count > 0:
                messages.warning(request, f'Failed to import {error_count} records. Check the format and try again.')
                for error in error_messages:
                    messages.error(request, error)

        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
            return redirect('certifications:upload_csv')

        return redirect('certifications:index')

    return render(request, 'upload_csv.html')

def verify(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    context = {'student': student}
    return render(request, 'student_verification.html', context)

def student_qr_info(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    # Add debug information to context
    context = {
        'student': student,
        'debug_info': {
            'student_id': student_id,
            'student_data': {
                'noms_et_prenoms': student.noms_et_prenoms,
                'matricule': student.matricule,
                'filiere': student.filiere,
                'mention': student.mention,
                'session': student.session,
                'sexe': student.sexe,
                'date_de_naissance': student.date_de_naissance,
                'lieu_de_naissance': student.lieu_de_naissance,
                'numero': student.numero,
                'issuer': student.issuer.name_en if student.issuer else None,
                'issue_date': student.issue_date,
            }
        }
    }
    return render(request, 'student_qr_info.html', context)

def download_qr_codes(request):
    students = Student.objects.all()
    
    # Create a CSV file with student data and QR code links
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow(['Noms et Prénoms', 'Matricule', 'Filière', 'Mention', 'Session', 'Sexe', 'Date de Naissance', 'Lieu de Naissance', 'Numéro', 'Issuer', 'Issue Date', 'QR Code Link'])
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for student in students:
            # Write student data to CSV
            csv_writer.writerow([
                student.noms_et_prenoms,
                student.matricule,
                student.filiere,
                student.mention,
                student.session,
                student.sexe,
                student.date_de_naissance,
                student.lieu_de_naissance,
                student.numero,
                student.issuer.name_en,
                student.issue_date,
                student.qr_code_link
            ])
            
            # Add QR code image to zip file if it exists
            if student.qr_code_link:
                qr_code_path = f'qr_codes/student_{student.id}.png'
                if default_storage.exists(qr_code_path):
                    with default_storage.open(qr_code_path, 'rb') as qr_file:
                        zip_file.writestr(f'qr_codes/student_{student.id}.png', qr_file.read())
        
        # Add CSV file to zip
        zip_file.writestr('student_data.csv', csv_buffer.getvalue())
    
    zip_buffer.seek(0)
    response = FileResponse(zip_buffer, as_attachment=True, filename='student_qr_codes_and_data.zip')
    return response

def manage_templates(request):
    templates = CertificateTemplate.objects.all()
    return render(request, 'manage_templates.html', {'templates': templates})

def create_template(request):
    if request.method == 'POST':
        form = CertificateTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificate template created successfully.')
            return redirect('certifications:manage_templates')
    else:
        form = CertificateTemplateForm()
    return render(request, 'template_form.html', {'form': form, 'action': 'Create'})

def edit_template(request, template_id):
    template = get_object_or_404(CertificateTemplate, id=template_id)
    if request.method == 'POST':
        form = CertificateTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificate template updated successfully.')
            return redirect('certifications:manage_templates')
    else:
        form = CertificateTemplateForm(instance=template)
    return render(request, 'template_form.html', {'form': form, 'action': 'Edit'})

def delete_template(request, template_id):
    template = get_object_or_404(CertificateTemplate, id=template_id)
    template.delete()
    messages.success(request, 'Certificate template deleted successfully.')
    return redirect('certifications:manage_templates')

def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            try:
                student = form.save()
                # Regenerate QR code if it doesn't exist
                if not student.qr_code_link:
                    qr_code_url = generate_qr_code(student.id)
                    student.qr_code_link = qr_code_url
                    student.save()
                messages.success(request, f'Student record updated for {student.noms_et_prenoms}')
                return redirect('certifications:index')
            except IntegrityError:
                messages.error(request, 'Error: This update would result in a duplicate record or QR code link.')
    else:
        form = StudentForm(instance=student)
    return render(request, 'student_form.html', {'form': form, 'action': 'Edit'})

def create_issuer(request):
    if request.method == 'POST':
        form = IssuerForm(request.POST, request.FILES)
        if form.is_valid():
            issuer = form.save()
            messages.success(request, f'Issuer {issuer.name_en} created successfully.')
            return redirect('certifications:list_issuers')  # Changed to redirect to issuer list
    else:
        form = IssuerForm()
    return render(request, 'issuer_form.html', {'form': form, 'action': 'Create'})

def edit_issuer(request, issuer_id):
    issuer = get_object_or_404(Issuer, id=issuer_id)
    if request.method == 'POST':
        form = IssuerForm(request.POST, request.FILES, instance=issuer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Issuer {issuer.name_en} updated successfully.')
            return redirect('certifications:list_issuers')  # Changed to redirect to issuer list
    else:
        form = IssuerForm(instance=issuer)
    return render(request, 'issuer_form.html', {'form': form, 'action': 'Edit'})

def list_issuers(request):
    issuers = Issuer.objects.all()
    return render(request, 'issuer_list.html', {'issuers': issuers})

def verify_issuer(request, uuid):
    issuer = get_object_or_404(Issuer, uuid=uuid)
    students = issuer.student_set.all()
    context = {
        'issuer': issuer,
        'students': students,
    }
    return render(request, 'verify_issuer.html', context)

def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # For GET requests, show the confirmation page
    if request.method == 'GET':
        return render(request, 'student_confirm_delete.html', {'student': student})
    
    # For POST requests, perform the deletion
    elif request.method == 'POST':
        # Delete the QR code file if it exists
        if student.qr_code_link:
            qr_code_path = f'qr_codes/student_{student.id}.png'
            if default_storage.exists(qr_code_path):
                default_storage.delete(qr_code_path)
        student.delete()
        messages.success(request, f'Student record deleted for {student.noms_et_prenoms}')
        return redirect('certifications:index')
