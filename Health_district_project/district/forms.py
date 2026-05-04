from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from district.models import Doctor, Hospital, Patient


class DateInput(forms.DateInput):
    input_type = 'date'


class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ['name', 'city', 'address', 'opened_date', 'notes']
        widgets = {
            'opened_date': DateInput(),
        }


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name', 'specialty', 'phone', 'is_active', 'hospitals']


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'phone',
            'hospital',
            'doctor',
            'admitted_on',
            'diagnosis',
            'is_discharged',
        ]
        widgets = {
            'date_of_birth': DateInput(),
            'admitted_on': DateInput(),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']