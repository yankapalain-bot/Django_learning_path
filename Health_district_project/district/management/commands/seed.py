from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from district.models import Doctor, Hospital, Patient


class Command(BaseCommand):
    help = "Seed the database with hospitals, doctors, and patients."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Clearing old data...")
        Patient.objects.all().delete()
        Doctor.objects.all().delete()
        Hospital.objects.all().delete()

        self.stdout.write("Creating hospitals...")
        h1 = Hospital.objects.create(
            name='North General Hospital',
            city='Toronto',
            address='100 North Street',
            opened_date=date(2010, 3, 15),
            notes='Main referral hospital for the northern district.',
        )
        h2 = Hospital.objects.create(
            name='Lakeside Medical Center',
            city='Toronto',
            address='22 Lake Avenue',
            opened_date=date(2014, 7, 2),
            notes='Busy outpatient and emergency center.',
        )
        h3 = Hospital.objects.create(
            name='West Valley Hospital',
            city='Mississauga',
            address='8 Valley Road',
            opened_date=date(2018, 1, 20),
            notes='Modern hospital with strong specialist teams.',
        )
        h4 = Hospital.objects.create(
            name='Eastview Community Hospital',
            city='Scarborough',
            address='77 Eastview Drive',
            opened_date=date(2021, 9, 5),
            notes='Community-focused hospital for family care.',
        )
        h5 = Hospital.objects.create(
            name='Westview City Hospital',
            city='Stony Plain',
            address='128St NW Drive',
            opened_date=date(2020, 3, 5),
            notes='City-focused hospital for citizens.',
        )

        self.stdout.write("Creating doctors...")
        d1 = Doctor.objects.create(first_name='Alice', last_name='Martin', specialty='Internal Medicine', phone='555-0101')
        d2 = Doctor.objects.create(first_name='Bob', last_name='Chen', specialty='Pediatrics', phone='555-0102')
        d3 = Doctor.objects.create(first_name='Carol', last_name='Patel', specialty='Cardiology', phone='555-0103')
        d4 = Doctor.objects.create(first_name='Daniel', last_name='Owusu', specialty='Emergency Medicine', phone='555-0104')
        d5 = Doctor.objects.create(first_name='Pat', last_name='Ehang', specialty='physician', phone='825-0106')        
        d6 = Doctor.objects.create(first_name='Yvy', last_name='Ngansop', specialty='Internal Medicine', phone='666-0101')
        d7 = Doctor.objects.create(first_name='Yuri', last_name='Yaakov', specialty='Pediatrics', phone='777-0102')
        d8 = Doctor.objects.create(first_name='Anne', last_name='Metok', specialty='Cardiology', phone='888-0103')
        d9 = Doctor.objects.create(first_name='Kery', last_name='Logan', specialty='Emergency Medicine', phone='999-0104')
        d10 = Doctor.objects.create(first_name='Sean', last_name='Kingston', specialty='physician', phone='578-0106')

        d1.hospitals.set([h1, h2])
        d2.hospitals.set([h1, h3])
        d3.hospitals.set([h2, h3, h4])
        d4.hospitals.set([h2, h5])
        d5.hospitals.set([h1, h3, h5])
        d6.hospitals.set([h1, h2])
        d7.hospitals.set([h1, h3])
        d8.hospitals.set([h2, h3, h4])
        d9.hospitals.set([h2, h5])
        d10.hospitals.set([h1, h3, h5])

        self.stdout.write("Creating patients...")
        Patient.objects.create(
            first_name='Emma',
            last_name='Brown',
            date_of_birth=date(1988, 4, 12),
            gender='female',
            phone='555-1101',
            hospital=h1,
            doctor=d5,
            admitted_on=date(2026, 4, 11),
            diagnosis='Hypertension follow-up',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Liam',
            last_name='Wilson',
            date_of_birth=date(2015, 8, 1),
            gender='male',
            phone='555-1102',
            hospital=h3,
            doctor=d5,
            admitted_on=date(2026, 4, 12),
            diagnosis='Fever and cough',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Noah',
            last_name='Taylor',
            date_of_birth=date(1979, 11, 23),
            gender='male',
            phone='555-1103',
            hospital=h5,
            doctor=d5,
            admitted_on=date(2026, 4, 9),
            diagnosis='Cardiac assessment',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Ava',
            last_name='Anderson',
            date_of_birth=date(1996, 2, 14),
            gender='female',
            phone='555-1104',
            hospital=h5,
            doctor=d5,
            admitted_on=date(2026, 4, 10),
            diagnosis='Abdominal pain',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Mason',
            last_name='Thomas',
            date_of_birth=date(2008, 6, 30),
            gender='male',
            phone='555-1105',
            hospital=h1,
            doctor=d10,
            admitted_on=date(2026, 4, 8),
            diagnosis='Sports injury',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Sophia',
            last_name='Moore',
            date_of_birth=date(1967, 10, 3),
            gender='female',
            phone='555-1106',
            hospital=h3,
            doctor=d10,
            admitted_on=date(2026, 4, 7),
            diagnosis='Blood pressure monitoring',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Ethan',
            last_name='Jackson',
            date_of_birth=date(1991, 12, 21),
            gender='male',
            phone='555-1107',
            hospital=h5,
            doctor=d10,
            admitted_on=date(2026, 4, 13),
            diagnosis='Emergency observation',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Emma',
            last_name='Brown',
            date_of_birth=date(1988, 4, 12),
            gender='female',
            phone='555-1101',
            hospital=h1,
            doctor=d1,
            admitted_on=date(2026, 4, 11),
            diagnosis='Hypertension follow-up',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Liam',
            last_name='Wilson',
            date_of_birth=date(2015, 8, 1),
            gender='male',
            phone='555-1102',
            hospital=h1,
            doctor=d2,
            admitted_on=date(2026, 4, 12),
            diagnosis='Fever and cough',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Noah',
            last_name='Taylor',
            date_of_birth=date(1979, 11, 23),
            gender='male',
            phone='555-1103',
            hospital=h2,
            doctor=d3,
            admitted_on=date(2026, 4, 9),
            diagnosis='Cardiac assessment',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Ava',
            last_name='Anderson',
            date_of_birth=date(1996, 2, 14),
            gender='female',
            phone='555-1104',
            hospital=h2,
            doctor=d1,
            admitted_on=date(2026, 4, 10),
            diagnosis='Abdominal pain',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Mason',
            last_name='Thomas',
            date_of_birth=date(2008, 6, 30),
            gender='male',
            phone='555-1105',
            hospital=h3,
            doctor=d2,
            admitted_on=date(2026, 4, 8),
            diagnosis='Sports injury',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Sophia',
            last_name='Moore',
            date_of_birth=date(1967, 10, 3),
            gender='female',
            phone='555-1106',
            hospital=h3,
            doctor=d3,
            admitted_on=date(2026, 4, 7),
            diagnosis='Blood pressure monitoring',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Ethan',
            last_name='Jackson',
            date_of_birth=date(1991, 12, 21),
            gender='male',
            phone='555-1107',
            hospital=h5,
            doctor=d4,
            admitted_on=date(2026, 4, 13),
            diagnosis='Emergency observation',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Olivia',
            last_name='White',
            date_of_birth=date(1982, 5, 18),
            gender='female',
            phone='555-1108',
            hospital=h4,
            doctor=d3,
            admitted_on=date(2026, 4, 6),
            diagnosis='Chest pain evaluation',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Alyve',
            last_name='Nguenou',
            date_of_birth=date(1982, 5, 18),
            gender='female',
            phone='555-1108',
            hospital=h5,
            doctor=d4,
            admitted_on=date(2026, 4, 6),
            diagnosis='Chest pain evaluation',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Olivia',
            last_name='White',
            date_of_birth=date(1982, 5, 18),
            gender='female',
            phone='555-1108',
            hospital=h4,
            doctor=d3,
            admitted_on=date(2026, 4, 6),
            diagnosis='Chest pain evaluation',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Emma',
            last_name='Brown',
            date_of_birth=date(1988, 4, 12),
            gender='female',
            phone='555-1101',
            hospital=h1,
            doctor=d6,
            admitted_on=date(2026, 4, 11),
            diagnosis='Hypertension follow-up',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Liam',
            last_name='Wilson',
            date_of_birth=date(2015, 8, 1),
            gender='male',
            phone='555-1102',
            hospital=h1,
            doctor=d7,
            admitted_on=date(2026, 4, 12),
            diagnosis='Fever and cough',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Noah',
            last_name='Taylor',
            date_of_birth=date(1979, 11, 23),
            gender='male',
            phone='555-1103',
            hospital=h2,
            doctor=d8,
            admitted_on=date(2026, 4, 9),
            diagnosis='Cardiac assessment',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Ava',
            last_name='Anderson',
            date_of_birth=date(1996, 2, 14),
            gender='female',
            phone='555-1104',
            hospital=h2,
            doctor=d6,
            admitted_on=date(2026, 4, 10),
            diagnosis='Abdominal pain',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Mason',
            last_name='Thomas',
            date_of_birth=date(2008, 6, 30),
            gender='male',
            phone='555-1105',
            hospital=h3,
            doctor=d7,
            admitted_on=date(2026, 4, 8),
            diagnosis='Sports injury',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Sophia',
            last_name='Moore',
            date_of_birth=date(1967, 10, 3),
            gender='female',
            phone='555-1106',
            hospital=h3,
            doctor=d8,
            admitted_on=date(2026, 4, 7),
            diagnosis='Blood pressure monitoring',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Ethan',
            last_name='Jackson',
            date_of_birth=date(1991, 12, 21),
            gender='male',
            phone='555-1107',
            hospital=h5,
            doctor=d9,
            admitted_on=date(2026, 4, 13),
            diagnosis='Emergency observation',
            is_discharged=False,
        )
        Patient.objects.create(
            first_name='Olivia',
            last_name='White',
            date_of_birth=date(1982, 5, 18),
            gender='female',
            phone='555-1108',
            hospital=h4,
            doctor=d8,
            admitted_on=date(2026, 4, 6),
            diagnosis='Chest pain evaluation',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Alyve',
            last_name='Nguenou',
            date_of_birth=date(1982, 5, 18),
            gender='female',
            phone='555-1108',
            hospital=h5,
            doctor=d9,
            admitted_on=date(2026, 4, 6),
            diagnosis='Chest pain evaluation',
            is_discharged=True,
        )
        Patient.objects.create(
            first_name='Olivia',
            last_name='White',
            date_of_birth=date(1982, 5, 18),
            gender='female',
            phone='555-1108',
            hospital=h4,
            doctor=d8,
            admitted_on=date(2026, 4, 6),
            diagnosis='Chest pain evaluation',
            is_discharged=True,
        )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))