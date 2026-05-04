# hrms/urls.py

from django.urls import path
from . import views

app_name = "hrms"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Departments
    path("departments/",                 views.DepartmentListView.as_view(),   name="department_list"),
    path("departments/create/",          views.DepartmentCreateView.as_view(), name="department_create"),
    path("departments/<int:pk>/",        views.DepartmentDetailView.as_view(), name="department_detail"),
    path("departments/<int:pk>/update/", views.DepartmentUpdateView.as_view(), name="department_update"),
    path("departments/<int:pk>/delete/", views.DepartmentDeleteView.as_view(), name="department_delete"),

    # Employees
    path("employees/",                   views.EmployeeListView.as_view(),   name="employee_list"),
    path("employees/create/",            views.EmployeeCreateView.as_view(), name="employee_create"),
    path("employees/<int:pk>/",          views.EmployeeDetailView.as_view(), name="employee_detail"),
    path("employees/<int:pk>/update/",   views.EmployeeUpdateView.as_view(), name="employee_update"),
    path("employees/<int:pk>/delete/",   views.EmployeeDeleteView.as_view(), name="employee_delete"),

    # Projects
    path("projects/",                    views.ProjectListView.as_view(),   name="project_list"),
    path("projects/create/",             views.ProjectCreateView.as_view(), name="project_create"),
    path("projects/<int:pk>/",           views.ProjectDetailView.as_view(), name="project_detail"),
    path("projects/<int:pk>/update/",    views.ProjectUpdateView.as_view(), name="project_update"),
    path("projects/<int:pk>/delete/",    views.ProjectDeleteView.as_view(), name="project_delete"),
]