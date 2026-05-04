# hrms/forms.py

from django import forms
from .models import Department, Employee, Project


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description", "parent"]


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "first_name", "last_name", "email", "title",
            "employee_type", "level", "department", "manager",
            "hire_date", "is_active", "bio",
        ]
        widgets = {
            "hire_date": forms.DateInput(attrs={"type": "date"}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name", "description", "status",
            "department", "lead", "members",
            "start_date", "end_date",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date":   forms.DateInput(attrs={"type": "date"}),
            "members":    forms.SelectMultiple(),
        }