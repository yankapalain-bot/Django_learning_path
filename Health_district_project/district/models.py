from django.db import models


class Hospital(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=200)
    opened_date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'{self.name} ({self.city})'


class Doctor(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    specialty = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    # Many-to-many: one doctor can work in many hospitals
    hospitals = models.ManyToManyField(
        Hospital,
        related_name='doctors',   # hospital.doctors.all()
    )

    def __str__(self):
        return f'{self.first_name} {self.last_name} — {self.specialty}'


class Patient(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='other')
    phone = models.CharField(max_length=20, blank=True)

    # ForeignKey: each patient belongs to one hospital
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='patients',   # hospital.patients.all()
    )

    # ForeignKey: each patient is handled by one doctor
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients',   # doctor.patients.all()
    )

    admitted_on = models.DateField()
    diagnosis = models.CharField(max_length=200)
    is_discharged = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'