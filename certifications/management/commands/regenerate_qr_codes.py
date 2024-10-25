from django.core.management.base import BaseCommand
from certifications.models import Student
from certifications.views import generate_qr_code

class Command(BaseCommand):
    help = 'Regenerates QR codes for all students with the correct URL'

    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        total = students.count()
        self.stdout.write(f'Found {total} students. Starting QR code regeneration...')

        for i, student in enumerate(students, 1):
            # Generate new QR code
            qr_code_url = generate_qr_code(student.id)
            student.qr_code_link = qr_code_url
            student.save()
            self.stdout.write(f'Processed {i}/{total}: {student.noms_et_prenoms}')

        self.stdout.write(self.style.SUCCESS('Successfully regenerated all QR codes'))
