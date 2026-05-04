from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from district.forms import DoctorForm, HospitalForm, PatientForm, RegisterForm
from district.models import Doctor, Hospital, Patient


def filter_patients(request):
    qs = Patient.objects.select_related('hospital', 'doctor').order_by('last_name', 'first_name')

    q = request.GET.get('q', '').strip()
    hospital_id = request.GET.get('hospital', '').strip()

    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(diagnosis__icontains=q)
            | Q(hospital__name__icontains=q)
            | Q(doctor__first_name__icontains=q)
            | Q(doctor__last_name__icontains=q)
        )

    if hospital_id:
        qs = qs.filter(hospital_id=hospital_id)

    return qs


def filter_doctors(request):
    qs = Doctor.objects.prefetch_related('hospitals').order_by('last_name', 'first_name')

    q = request.GET.get('q', '').strip()

    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(specialty__icontains=q)
            | Q(hospitals__name__icontains=q)
        ).distinct()

    return qs


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'district/auth/register.html'
    success_url = reverse_lazy('hospital-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.email = form.cleaned_data.get('email', '')
        self.object.save(update_fields=['email'])
        login(self.request, self.object)
        return response


# ── Hospitals ───────────────────────────────────────────────────────────────

class HospitalListView(LoginRequiredMixin, ListView):
    model = Hospital
    template_name = 'district/hospital_list.html'
    context_object_name = 'hospitals'

    queryset = Hospital.objects.annotate(
        patient_count=Count('patients', distinct=True),
        doctor_count=Count('doctors', distinct=True),
    ).order_by('name')


class HospitalDetailView(LoginRequiredMixin, DetailView):
    model = Hospital
    template_name = 'district/hospital_detail.html'
    context_object_name = 'hospital'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['patients'] = self.object.patients.select_related('doctor').order_by('last_name', 'first_name')
        ctx['doctors'] = self.object.doctors.prefetch_related('hospitals').order_by('last_name', 'first_name')
        return ctx


class HospitalCreateView(LoginRequiredMixin, CreateView):
    model = Hospital
    form_class = HospitalForm
    template_name = 'district/hospital_form.html'
    success_url = reverse_lazy('hospital-list')


class HospitalUpdateView(LoginRequiredMixin, UpdateView):
    model = Hospital
    form_class = HospitalForm
    template_name = 'district/hospital_form.html'
    success_url = reverse_lazy('hospital-list')


class HospitalDeleteView(LoginRequiredMixin, DeleteView):
    model = Hospital
    template_name = 'district/hospital_confirm_delete.html'
    success_url = reverse_lazy('hospital-list')


# ── Doctors ─────────────────────────────────────────────────────────────────

class DoctorListView(LoginRequiredMixin, ListView):
    model = Doctor
    template_name = 'district/doctor_list.html'
    context_object_name = 'doctors'

    queryset = Doctor.objects.prefetch_related('hospitals').annotate(
        patient_count=Count('patients', distinct=True),
    ).order_by('last_name', 'first_name')


class DoctorDetailView(LoginRequiredMixin, DetailView):
    model = Doctor
    template_name = 'district/doctor_detail.html'
    context_object_name = 'doctor'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['hospitals'] = self.object.hospitals.order_by('name')
        ctx['patients'] = self.object.patients.select_related('hospital').order_by('last_name', 'first_name')
        return ctx


class DoctorCreateView(LoginRequiredMixin, CreateView):
    model = Doctor
    form_class = DoctorForm
    template_name = 'district/doctor_form.html'
    success_url = reverse_lazy('doctor-list')


class DoctorUpdateView(LoginRequiredMixin, UpdateView):
    model = Doctor
    form_class = DoctorForm
    template_name = 'district/doctor_form.html'
    success_url = reverse_lazy('doctor-list')


class DoctorDeleteView(LoginRequiredMixin, DeleteView):
    model = Doctor
    template_name = 'district/doctor_confirm_delete.html'
    success_url = reverse_lazy('doctor-list')


class DoctorSearchView(LoginRequiredMixin, ListView):
    model = Doctor
    template_name = 'district/partials/doctor_table.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        return filter_doctors(self.request)


# ── Patients ────────────────────────────────────────────────────────────────

class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'district/patient_list.html'
    context_object_name = 'patients'

    queryset = Patient.objects.select_related('hospital', 'doctor').order_by('last_name', 'first_name')
    paginate_by = None  # set to 10 later as an extension

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['hospitals'] = Hospital.objects.order_by('name')
        return ctx


class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = 'district/patient_detail.html'
    context_object_name = 'patient'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.doctor_id:
            ctx['doctor_other_patients'] = (
                self.object.doctor.patients
                .exclude(pk=self.object.pk)
                .select_related('hospital')
                .order_by('last_name', 'first_name')
            )
        else:
            ctx['doctor_other_patients'] = Patient.objects.none()
        return ctx


class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'district/patient_form.html'
    success_url = reverse_lazy('patient-list')


class PatientUpdateView(LoginRequiredMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = 'district/patient_form.html'
    success_url = reverse_lazy('patient-list')


class PatientDeleteView(LoginRequiredMixin, DeleteView):
    model = Patient
    template_name = 'district/patient_confirm_delete.html'
    success_url = reverse_lazy('patient-list')


class PatientInlineDeleteView(LoginRequiredMixin, DeleteView):
    model = Patient

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse('')


class PatientSearchView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'district/partials/patient_table.html'
    context_object_name = 'patients'

    def get_queryset(self):
        return filter_patients(self.request)


class HospitalFilterView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'district/partials/patient_table.html'
    context_object_name = 'patients'

    def get_queryset(self):
        return filter_patients(self.request)