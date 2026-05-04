from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from district import views

urlpatterns = [
    # Auth
    path('login/', LoginView.as_view(template_name='district/auth/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Hospitals
    path('', views.HospitalListView.as_view(), name='hospital-list'),
    path('hospitals/add/', views.HospitalCreateView.as_view(), name='hospital-create'),
    path('hospitals/<int:pk>/', views.HospitalDetailView.as_view(), name='hospital-detail'),
    path('hospitals/<int:pk>/edit/', views.HospitalUpdateView.as_view(), name='hospital-update'),
    path('hospitals/<int:pk>/delete/', views.HospitalDeleteView.as_view(), name='hospital-delete'),

    # Doctors
    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('doctors/add/', views.DoctorCreateView.as_view(), name='doctor-create'),
    path('doctors/search/', views.DoctorSearchView.as_view(), name='doctor-search'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    path('doctors/<int:pk>/edit/', views.DoctorUpdateView.as_view(), name='doctor-update'),
    path('doctors/<int:pk>/delete/', views.DoctorDeleteView.as_view(), name='doctor-delete'),

    # Patients
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/add/', views.PatientCreateView.as_view(), name='patient-create'),
    path('patients/search/', views.PatientSearchView.as_view(), name='patient-search'),
    path('patients/filter/', views.HospitalFilterView.as_view(), name='patient-filter'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),
    path('patients/<int:pk>/edit/', views.PatientUpdateView.as_view(), name='patient-update'),
    path('patients/<int:pk>/delete/', views.PatientDeleteView.as_view(), name='patient-delete'),
    path('patients/<int:pk>/inline-delete/', views.PatientInlineDeleteView.as_view(), name='patient-inline-delete'),
]