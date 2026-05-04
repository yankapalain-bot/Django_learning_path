# Building a Django HR Management Dashboard with HTMX
### (Class-Based Views Edition)

A complete guide to building a full-CRUD Human Resources dashboard modeled after a large tech company (Alphabet Inc.) hierarchy — no CSS styling, HTMX for all HTTP interactions, Django's ORM for hierarchical employee data, and **Generic Class-Based Views** throughout.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Setup](#2-project-setup)
3. [App Structure](#3-app-structure)
4. [Models](#4-models)
5. [Database Migrations](#5-database-migrations)
6. [Fake Data Seed Script](#6-fake-data-seed-script)
7. [Forms](#7-forms)
8. [Views](#8-views)
9. [URL Configuration](#9-url-configuration)
10. [Templates](#10-templates)
11. [HTMX & CSRF Setup](#11-htmx--csrf-setup)
12. [Running the Project](#12-running-the-project)

---

## 1. Prerequisites

- Python 3.11+
- pip
- virtualenv (recommended)

```bash
pip install django faker
```

---

## 2. Project Setup

```bash
django-admin startproject hrms_project
cd hrms_project
python manage.py startapp hrms
```

Add `hrms` to `INSTALLED_APPS` in `hrms_project/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'hrms',
]
```

---

## 3. App Structure

```
hrms_project/
├── hrms_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── hrms/
│   ├── migrations/
│   ├── templates/
│   │   └── hrms/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── employees/
│   │       │   ├── employee_list.html
│   │       │   ├── employee_detail.html
│   │       │   ├── employee_form.html
│   │       │   └── employee_confirm_delete.html
│   │       ├── departments/
│   │       │   ├── department_list.html
│   │       │   ├── department_detail.html
│   │       │   ├── department_form.html
│   │       │   └── department_confirm_delete.html
│   │       └── projects/
│   │           ├── project_list.html
│   │           ├── project_detail.html
│   │           ├── project_form.html
│   │           └── project_confirm_delete.html
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── seed_data.py
└── manage.py
```

> **Template naming convention:** Django's generic CBVs auto-resolve template names as
> `<app_label>/<model_name_lowercase>_<suffix>.html`. Matching this convention means
> you never have to set `template_name` explicitly on most views.

---

## 4. Models

`hrms/models.py` is unchanged from the function-based version. It is reproduced here for completeness.

```python
# hrms/models.py

from django.db import models


# ─────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────

class EmployeeLevel(models.TextChoices):
    # Individual Contributors
    L1 = "L1", "L1 – Associate"
    L2 = "L2", "L2 – Junior"
    L3 = "L3", "L3 – Mid-Level"
    L4 = "L4", "L4 – Senior IC"
    # Middle Management
    SPM = "SPM", "Senior Product Manager"
    GROUP_MANAGER = "GM", "Group Manager"
    # Senior Leadership
    DIRECTOR = "DIR", "Director"
    SVP = "SVP", "Senior Vice President"
    # C-Suite
    VP = "VP", "Vice President"
    CEO = "CEO", "Chief Executive Officer"
    CFO = "CFO", "Chief Financial Officer"
    CTO = "CTO", "Chief Technology Officer"
    COO = "COO", "Chief Operating Officer"


class EmployeeType(models.TextChoices):
    INDIVIDUAL_CONTRIBUTOR = "IC", "Individual Contributor"
    MIDDLE_MANAGEMENT = "MM", "Middle Management"
    SENIOR_LEADERSHIP = "SL", "Senior Leadership"
    C_SUITE = "CS", "C-Suite"


class ProjectStatus(models.TextChoices):
    PLANNING = "PLAN", "Planning"
    ACTIVE = "ACTIVE", "Active"
    ON_HOLD = "HOLD", "On Hold"
    COMPLETED = "DONE", "Completed"
    CANCELLED = "CANC", "Cancelled"


# ─────────────────────────────────────────────
# Department
# ─────────────────────────────────────────────

class Department(models.Model):
    """
    Represents a business unit (e.g., Google Search, YouTube, Google Cloud).
    Departments can be nested: a sub-department points to a parent department.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sub_departments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("hrms:department_detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["name"]


# ─────────────────────────────────────────────
# Employee
# ─────────────────────────────────────────────

class Employee(models.Model):
    """
    Unified employee model covering all four tiers of the Alphabet hierarchy.

    Relationships:
      - manager (self-referential FK): direct reporting line
      - department (FK): the primary business unit the employee belongs to
      - direct_reports: reverse of manager FK — employees who report to this person
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    title = models.CharField(max_length=200)
    employee_type = models.CharField(
        max_length=2,
        choices=EmployeeType.choices,
        default=EmployeeType.INDIVIDUAL_CONTRIBUTOR,
    )
    level = models.CharField(
        max_length=5,
        choices=EmployeeLevel.choices,
        default=EmployeeLevel.L1,
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="employees",
    )
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.level})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("hrms:employee_detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["last_name", "first_name"]


# ─────────────────────────────────────────────
# Project
# ─────────────────────────────────────────────

class Project(models.Model):
    """
    A business initiative that spans one or more departments and employees.

    Relationships:
      - department (FK): the owning / sponsoring department
      - lead (FK → Employee): the employee accountable for delivery
      - members (M2M → Employee): all employees contributing to the project
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=6,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PLANNING,
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    lead = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="led_projects",
    )
    members = models.ManyToManyField(
        Employee,
        blank=True,
        related_name="projects",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("hrms:project_detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["name"]
```

> **`get_absolute_url`** is added to each model. `CreateView` and `UpdateView` call it
> automatically after a successful save when no `success_url` is defined, which keeps
> the redirect logic inside the model rather than scattered across views.

### Relationship Summary

| Relationship | From | To | Type |
|---|---|---|---|
| Reporting line | `Employee.manager` | `Employee` | FK (self) |
| Primary unit | `Employee.department` | `Department` | FK |
| Sub-unit | `Department.parent` | `Department` | FK (self) |
| Project ownership | `Project.department` | `Department` | FK |
| Project accountability | `Project.lead` | `Employee` | FK |
| Project contribution | `Project.members` | `Employee` | M2M |

---

## 5. Database Migrations

```bash
python manage.py makemigrations hrms
python manage.py migrate
```

---

## 6. Fake Data Seed Script

Unchanged from the function-based version — seed data has no dependency on the view layer.

```python
# seed_data.py
"""
Populate the HRMS database with fake Alphabet-style data.
Run with:  python manage.py shell < seed_data.py
  or:      python seed_data.py   (from the project root with DJANGO_SETTINGS_MODULE set)
"""

import os
import sys
import django
import random
from datetime import date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_project.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from faker import Faker
from hrms.models import Department, Employee, Project, EmployeeLevel, EmployeeType, ProjectStatus

fake = Faker()
Faker.seed(42)
random.seed(42)

# ── Wipe existing data ────────────────────────────────────────────────────────
Project.objects.all().delete()
Employee.objects.all().delete()
Department.objects.all().delete()

# ── Departments ───────────────────────────────────────────────────────────────
top_level_departments = [
    "Google Search", "YouTube", "Google Cloud", "Google Ads", "Hardware",
    "AI Research (DeepMind)", "Android & Chrome", "Finance",
    "Legal & Policy", "People Operations",
]

sub_department_map = {
    "Google Search":          ["Search Quality", "Search Infrastructure", "Knowledge Graph"],
    "YouTube":                ["YouTube Premium", "YouTube Kids", "Creator Ecosystem"],
    "Google Cloud":           ["GKE & Compute", "BigQuery & Analytics", "Cloud Security"],
    "Google Ads":             ["Performance Max", "Display & Video 360", "Ad Tech Platform"],
    "Hardware":               ["Pixel Phones", "Nest & Home", "Fitbit"],
    "AI Research (DeepMind)": ["Gemini", "Robotics", "Safety Research"],
    "Android & Chrome":       ["Android OS", "Chrome Browser", "ChromeOS"],
    "Finance":                ["FP&A", "Tax", "Treasury"],
    "Legal & Policy":         ["Privacy & Compliance", "Litigation", "Government Affairs"],
    "People Operations":      ["Talent Acquisition", "L&D", "Total Rewards"],
}

dept_objects = {}
for name in top_level_departments:
    d = Department.objects.create(name=name, description=fake.sentence())
    dept_objects[name] = d
    for sub_name in sub_department_map.get(name, []):
        s = Department.objects.create(name=sub_name, description=fake.sentence(), parent=d)
        dept_objects[sub_name] = s

all_depts = list(Department.objects.filter(parent__isnull=False))

# ── C-Suite ───────────────────────────────────────────────────────────────────
c_suite_data = [
    ("Sundar",    "Pichai",   "CEO", EmployeeLevel.CEO, EmployeeType.C_SUITE, "Chief Executive Officer"),
    ("Ruth",      "Porat",    "CFO", EmployeeLevel.CFO, EmployeeType.C_SUITE, "Chief Financial Officer"),
    ("Prabhakar", "Raghavan", "CTO", EmployeeLevel.CTO, EmployeeType.C_SUITE, "Chief Technology Officer"),
]

c_suite_employees = []
for fn, ln, abbr, level, etype, title in c_suite_data:
    e = Employee.objects.create(
        first_name=fn, last_name=ln,
        email=f"{fn.lower()}.{ln.lower()}@alphabet.com",
        title=title, employee_type=etype, level=level,
        department=dept_objects["Google Search"],
        hire_date=date(2015, 1, 1),
        bio=fake.paragraph(),
    )
    c_suite_employees.append(e)

ceo = c_suite_employees[0]

# ── SVPs ──────────────────────────────────────────────────────────────────────
svp_employees = []
for top_dept_name in list(top_level_departments)[:6]:
    dept = dept_objects[top_dept_name]
    e = Employee.objects.create(
        first_name=fake.first_name(), last_name=fake.last_name(),
        email=fake.unique.company_email(),
        title=f"SVP, {top_dept_name}",
        employee_type=EmployeeType.SENIOR_LEADERSHIP,
        level=EmployeeLevel.SVP,
        department=dept, manager=ceo,
        hire_date=fake.date_between(start_date="-12y", end_date="-6y"),
        bio=fake.paragraph(),
    )
    svp_employees.append((dept, e))

# ── Directors ─────────────────────────────────────────────────────────────────
director_employees = []
for parent_dept, svp in svp_employees:
    for sub_dept in parent_dept.sub_departments.all():
        e = Employee.objects.create(
            first_name=fake.first_name(), last_name=fake.last_name(),
            email=fake.unique.company_email(),
            title=f"Director, {sub_dept.name}",
            employee_type=EmployeeType.SENIOR_LEADERSHIP,
            level=EmployeeLevel.DIRECTOR,
            department=sub_dept, manager=svp,
            hire_date=fake.date_between(start_date="-10y", end_date="-4y"),
            bio=fake.paragraph(),
        )
        director_employees.append((sub_dept, e))

# ── Middle Management ─────────────────────────────────────────────────────────
manager_employees = []
for sub_dept, director in director_employees:
    for _ in range(random.randint(2, 3)):
        level = random.choice([EmployeeLevel.SPM, EmployeeLevel.GROUP_MANAGER])
        title = "Senior Product Manager" if level == EmployeeLevel.SPM else "Group Manager"
        e = Employee.objects.create(
            first_name=fake.first_name(), last_name=fake.last_name(),
            email=fake.unique.company_email(),
            title=f"{title}, {sub_dept.name}",
            employee_type=EmployeeType.MIDDLE_MANAGEMENT,
            level=level, department=sub_dept, manager=director,
            hire_date=fake.date_between(start_date="-8y", end_date="-2y"),
            bio=fake.paragraph(),
        )
        manager_employees.append((sub_dept, e))

# ── Individual Contributors ───────────────────────────────────────────────────
ic_levels = [EmployeeLevel.L1, EmployeeLevel.L2, EmployeeLevel.L3, EmployeeLevel.L4]
ic_titles = {
    EmployeeLevel.L1: "Associate Software Engineer",
    EmployeeLevel.L2: "Software Engineer",
    EmployeeLevel.L3: "Senior Software Engineer",
    EmployeeLevel.L4: "Staff Software Engineer",
}

ic_employees = []
for sub_dept, mgr in manager_employees:
    for _ in range(random.randint(3, 6)):
        level = random.choice(ic_levels)
        e = Employee.objects.create(
            first_name=fake.first_name(), last_name=fake.last_name(),
            email=fake.unique.company_email(),
            title=ic_titles[level],
            employee_type=EmployeeType.INDIVIDUAL_CONTRIBUTOR,
            level=level, department=sub_dept, manager=mgr,
            hire_date=fake.date_between(start_date="-5y", end_date="today"),
            bio=fake.paragraph(),
        )
        ic_employees.append(e)

print(f"Employees created: {Employee.objects.count()}")

# ── Projects ──────────────────────────────────────────────────────────────────
all_managers   = [e for _, e in manager_employees]
all_employees  = list(Employee.objects.all())

project_names = [
    "Project Monarch", "Gemini Ultra Rollout", "Pixel 9 Launch",
    "Cloud Cost Optimisation", "YouTube Shorts Monetisation",
    "Search Ranking v3", "SafeSearch Overhaul", "Nest Thermostat AI",
    "BigQuery ML Integration", "Chrome Memory Saver",
    "Android Privacy Sandbox", "Ad Attribution Rebuild",
    "DeepMind Safety Audit", "Global Talent Pipeline",
    "Carbon Neutral Datacenters",
]

for proj_name in project_names:
    dept   = random.choice(all_depts)
    lead   = random.choice(all_managers)
    start  = fake.date_between(start_date="-2y", end_date="today")
    end    = start + timedelta(days=random.randint(90, 540))
    status = random.choice(list(ProjectStatus.values))

    project = Project.objects.create(
        name=proj_name,
        description=fake.paragraph(nb_sentences=3),
        status=status, department=dept, lead=lead,
        start_date=start, end_date=end,
    )
    members = random.sample(all_employees, k=random.randint(5, 15))
    if lead not in members:
        members.append(lead)
    project.members.set(members)

print(f"Projects created: {Project.objects.count()}")
print("Seed complete.")
```

Run the seed script:

```bash
python seed_data.py
```

---

## 7. Forms

Unchanged — forms have no dependency on the view type.

```python
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
```

---

## 8. Views

This is the section that changes entirely. Every view is now a class that inherits from one of Django's generic CBVs. The HTMX detection logic lives in overridden methods (`form_valid`, `delete`, `get_queryset`, `get_context_data`) rather than inside `if/else` branches.

### CBV–to–generic mapping

| Operation | Generic CBV used |
|---|---|
| Dashboard | `TemplateView` |
| List + search | `ListView` |
| Detail | `DetailView` |
| Create | `CreateView` |
| Update | `UpdateView` |
| Delete | `DeleteView` |

```python
# hrms/views.py

from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, DetailView,
    CreateView, UpdateView, DeleteView,
)

from .models import Department, Employee, Project, EmployeeLevel, ProjectStatus
from .forms import DepartmentForm, EmployeeForm, ProjectForm


# ── Shared mixin ──────────────────────────────────────────────────────────────

class HtmxResponseMixin:
    """
    Override form_valid / delete to return a lightweight HTML fragment
    when the request comes from HTMX, instead of a full redirect response.
    Subclasses set `htmx_success_message` as a callable or plain string.
    """

    def htmx_response(self, message: str) -> HttpResponse:
        return HttpResponse(message)

    def is_htmx(self) -> bool:
        return self.request.headers.get("HX-Request") == "true"


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

class DashboardView(TemplateView):
    template_name = "hrms/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["employee_count"]   = Employee.objects.filter(is_active=True).count()
        ctx["department_count"] = Department.objects.count()
        ctx["project_count"]    = Project.objects.count()
        ctx["recent_employees"] = Employee.objects.order_by("-created_at")[:5]
        ctx["active_projects"]  = Project.objects.filter(status="ACTIVE")[:5]
        return ctx


# ══════════════════════════════════════════════════════════════════════════════
# DEPARTMENT VIEWS
# ══════════════════════════════════════════════════════════════════════════════

class DepartmentListView(ListView):
    model = Department
    # resolves to hrms/department_list.html
    context_object_name = "departments"

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        if q:
            return Department.objects.filter(name__icontains=q)
        return Department.objects.filter(parent__isnull=True).prefetch_related("sub_departments")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request"):
            from django.template.response import TemplateResponse
            return TemplateResponse(
                self.request,
                "hrms/departments/_table_rows.html",
                context,
            )
        return super().render_to_response(context, **response_kwargs)


class DepartmentDetailView(DetailView):
    model = Department
    # resolves to hrms/department_detail.html
    context_object_name = "dept"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dept = self.object
        ctx["employees"]  = dept.employees.select_related("manager")
        ctx["projects"]   = dept.projects.all()
        ctx["sub_depts"]  = dept.sub_departments.all()
        return ctx


class DepartmentCreateView(HtmxResponseMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    # resolves to hrms/department_form.html

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Create"
        return ctx

    def form_valid(self, form):
        dept = form.save()
        if self.is_htmx():
            return self.htmx_response(
                f'<p>Department <strong>{dept.name}</strong> created. '
                f'<a href="{dept.get_absolute_url()}">View</a></p>'
            )
        return super().form_valid(form)


class DepartmentUpdateView(HtmxResponseMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    # resolves to hrms/department_form.html

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Update"
        return ctx

    def form_valid(self, form):
        dept = form.save()
        if self.is_htmx():
            return self.htmx_response(
                f'<p>Department <strong>{dept.name}</strong> updated. '
                f'<a href="{dept.get_absolute_url()}">View</a></p>'
            )
        return super().form_valid(form)


class DepartmentDeleteView(HtmxResponseMixin, DeleteView):
    model = Department
    success_url = reverse_lazy("hrms:department_list")
    # resolves to hrms/department_confirm_delete.html

    def delete(self, request, *args, **kwargs):
        dept = self.get_object()
        name = dept.name
        dept.delete()
        if self.is_htmx():
            return self.htmx_response(f'<p>Department <strong>{name}</strong> deleted.</p>')
        from django.shortcuts import redirect
        return redirect(self.success_url)

    # Django 4.0+ uses post() instead of delete(); support both:
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEE VIEWS
# ══════════════════════════════════════════════════════════════════════════════

class EmployeeListView(ListView):
    model = Employee
    # resolves to hrms/employee_list.html
    context_object_name = "employees"

    def get_queryset(self):
        qs = Employee.objects.select_related("department", "manager")
        q       = self.request.GET.get("q", "")
        level   = self.request.GET.get("level", "")
        dept_id = self.request.GET.get("dept", "")

        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
            )
        if level:
            qs = qs.filter(level=level)
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"]             = self.request.GET.get("q", "")
        ctx["level"]         = self.request.GET.get("level", "")
        ctx["dept_id"]       = self.request.GET.get("dept", "")
        ctx["departments"]   = Department.objects.all()
        ctx["level_choices"] = EmployeeLevel.choices
        return ctx

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request"):
            from django.template.response import TemplateResponse
            return TemplateResponse(
                self.request,
                "hrms/employees/_table_rows.html",
                context,
            )
        return super().render_to_response(context, **response_kwargs)


class EmployeeDetailView(DetailView):
    model = Employee
    # resolves to hrms/employee_detail.html
    context_object_name = "emp"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        emp = self.object
        ctx["direct_reports"] = emp.direct_reports.select_related("department")
        ctx["projects"]       = emp.projects.all()
        ctx["led_projects"]   = emp.led_projects.all()
        return ctx


class EmployeeCreateView(HtmxResponseMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    # resolves to hrms/employee_form.html

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Create"
        return ctx

    def form_valid(self, form):
        emp = form.save()
        if self.is_htmx():
            return self.htmx_response(
                f'<p>Employee <strong>{emp.full_name}</strong> created. '
                f'<a href="{emp.get_absolute_url()}">View</a></p>'
            )
        return super().form_valid(form)


class EmployeeUpdateView(HtmxResponseMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    # resolves to hrms/employee_form.html

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Update"
        return ctx

    def form_valid(self, form):
        emp = form.save()
        if self.is_htmx():
            return self.htmx_response(
                f'<p>Employee <strong>{emp.full_name}</strong> updated. '
                f'<a href="{emp.get_absolute_url()}">View</a></p>'
            )
        return super().form_valid(form)


class EmployeeDeleteView(HtmxResponseMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy("hrms:employee_list")
    # resolves to hrms/employee_confirm_delete.html

    def delete(self, request, *args, **kwargs):
        emp  = self.get_object()
        name = emp.full_name
        emp.delete()
        if self.is_htmx():
            return self.htmx_response(f'<p>Employee <strong>{name}</strong> deleted.</p>')
        from django.shortcuts import redirect
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT VIEWS
# ══════════════════════════════════════════════════════════════════════════════

class ProjectListView(ListView):
    model = Project
    # resolves to hrms/project_list.html
    context_object_name = "projects"

    def get_queryset(self):
        qs     = Project.objects.select_related("department", "lead")
        q      = self.request.GET.get("q", "")
        status = self.request.GET.get("status", "")
        if q:
            qs = qs.filter(name__icontains=q)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"]              = self.request.GET.get("q", "")
        ctx["status"]         = self.request.GET.get("status", "")
        ctx["status_choices"] = ProjectStatus.choices
        return ctx

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("HX-Request"):
            from django.template.response import TemplateResponse
            return TemplateResponse(
                self.request,
                "hrms/projects/_table_rows.html",
                context,
            )
        return super().render_to_response(context, **response_kwargs)


class ProjectDetailView(DetailView):
    model = Project
    # resolves to hrms/project_detail.html
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["members"] = self.object.members.select_related("department")
        return ctx


class ProjectCreateView(HtmxResponseMixin, CreateView):
    model = Project
    form_class = ProjectForm
    # resolves to hrms/project_form.html

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Create"
        return ctx

    def form_valid(self, form):
        project = form.save()
        if self.is_htmx():
            return self.htmx_response(
                f'<p>Project <strong>{project.name}</strong> created. '
                f'<a href="{project.get_absolute_url()}">View</a></p>'
            )
        return super().form_valid(form)


class ProjectUpdateView(HtmxResponseMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    # resolves to hrms/project_form.html

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action"] = "Update"
        return ctx

    def form_valid(self, form):
        project = form.save()
        if self.is_htmx():
            return self.htmx_response(
                f'<p>Project <strong>{project.name}</strong> updated. '
                f'<a href="{project.get_absolute_url()}">View</a></p>'
            )
        return super().form_valid(form)


class ProjectDeleteView(HtmxResponseMixin, DeleteView):
    model = Project
    success_url = reverse_lazy("hrms:project_list")
    # resolves to hrms/project_confirm_delete.html

    def delete(self, request, *args, **kwargs):
        project = self.get_object()
        name    = project.name
        project.delete()
        if self.is_htmx():
            return self.htmx_response(f'<p>Project <strong>{name}</strong> deleted.</p>')
        from django.shortcuts import redirect
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
```

---

## 9. URL Configuration

`as_view()` is called on each class. Everything else is identical to the function-based version.

### `hrms/urls.py`

```python
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
```

### `hrms_project/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("hrms.urls", namespace="hrms")),
]
```

---

## 10. Templates

> **Naming change from the function-based version:** Django's generic CBVs resolve
> templates as `<app_label>/<model_name>_<suffix>.html`. The previous guide used a
> custom sub-folder layout (`employees/list.html`). Here we match the CBV convention
> exactly so `template_name` never needs to be set on any view.

### `hrms/templates/hrms/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{% block title %}HR Dashboard{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
</head>
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

<nav>
  <a href="{% url 'hrms:dashboard' %}">Dashboard</a> |
  <a href="{% url 'hrms:employee_list' %}">Employees</a> |
  <a href="{% url 'hrms:department_list' %}">Departments</a> |
  <a href="{% url 'hrms:project_list' %}">Projects</a>
</nav>

<hr>

<div id="main-content">
  {% block content %}{% endblock %}
</div>

</body>
</html>
```

---

### `hrms/templates/hrms/dashboard.html`

```html
{% extends "hrms/base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h1>HR Dashboard</h1>

<p>Active Employees: {{ employee_count }}</p>
<p>Departments: {{ department_count }}</p>
<p>Projects: {{ project_count }}</p>

<h2>Recently Added Employees</h2>
<ul>
  {% for emp in recent_employees %}
    <li>
      <a href="{% url 'hrms:employee_detail' emp.pk %}">{{ emp.full_name }}</a>
      — {{ emp.title }}
    </li>
  {% endfor %}
</ul>

<h2>Active Projects</h2>
<ul>
  {% for proj in active_projects %}
    <li>
      <a href="{% url 'hrms:project_detail' proj.pk %}">{{ proj.name }}</a>
      ({{ proj.department }})
    </li>
  {% endfor %}
</ul>
{% endblock %}
```

---

### Department Templates

#### `hrms/templates/hrms/department_list.html`

```html
{% extends "hrms/base.html" %}
{% block title %}Departments{% endblock %}
{% block content %}
<h1>Departments</h1>

<a href="{% url 'hrms:department_create' %}">+ New Department</a>

<form>
  <input
    type="text"
    name="q"
    value="{{ q }}"
    placeholder="Search departments…"
    hx-get="{% url 'hrms:department_list' %}"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#dept-rows"
    hx-swap="innerHTML"
  >
</form>

<table border="1">
  <thead>
    <tr>
      <th>Name</th>
      <th>Parent</th>
      <th>Sub-departments</th>
      <th>Employees</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody id="dept-rows">
    {% include "hrms/departments/_table_rows.html" %}
  </tbody>
</table>
{% endblock %}
```

#### `hrms/templates/hrms/departments/_table_rows.html`

```html
{% for dept in departments %}
<tr>
  <td><a href="{% url 'hrms:department_detail' dept.pk %}">{{ dept.name }}</a></td>
  <td>
    {% if dept.parent %}
      <a href="{% url 'hrms:department_detail' dept.parent.pk %}">{{ dept.parent.name }}</a>
    {% else %}—{% endif %}
  </td>
  <td>{{ dept.sub_departments.count }}</td>
  <td>{{ dept.employees.count }}</td>
  <td>
    <a href="{% url 'hrms:department_update' dept.pk %}">Edit</a> |
    <button
      hx-delete="{% url 'hrms:department_delete' dept.pk %}"
      hx-target="closest tr"
      hx-swap="outerHTML"
      hx-confirm="Delete department {{ dept.name }}?"
    >Delete</button>
  </td>
</tr>
{% empty %}
<tr><td colspan="5">No departments found.</td></tr>
{% endfor %}
```

#### `hrms/templates/hrms/department_detail.html`

```html
{% extends "hrms/base.html" %}
{% block title %}{{ dept.name }}{% endblock %}
{% block content %}
<h1>{{ dept.name }}</h1>

{% if dept.parent %}
  <p>Parent: <a href="{% url 'hrms:department_detail' dept.parent.pk %}">{{ dept.parent.name }}</a></p>
{% else %}
  <p>Top-level department</p>
{% endif %}

<p>{{ dept.description }}</p>

<p>
  <a href="{% url 'hrms:department_update' dept.pk %}">Edit</a> |
  <button
    hx-delete="{% url 'hrms:department_delete' dept.pk %}"
    hx-target="#delete-result"
    hx-swap="innerHTML"
    hx-confirm="Permanently delete {{ dept.name }}?"
  >Delete</button>
</p>
<div id="delete-result"></div>

<h2>Sub-departments ({{ sub_depts.count }})</h2>
<ul>
  {% for sub in sub_depts %}
    <li><a href="{% url 'hrms:department_detail' sub.pk %}">{{ sub.name }}</a></li>
  {% empty %}
    <li>None</li>
  {% endfor %}
</ul>

<h2>Employees ({{ employees.count }})</h2>
<table border="1">
  <thead>
    <tr><th>Name</th><th>Title</th><th>Level</th><th>Manager</th></tr>
  </thead>
  <tbody>
    {% for emp in employees %}
    <tr>
      <td><a href="{% url 'hrms:employee_detail' emp.pk %}">{{ emp.full_name }}</a></td>
      <td>{{ emp.title }}</td>
      <td>{{ emp.get_level_display }}</td>
      <td>
        {% if emp.manager %}
          <a href="{% url 'hrms:employee_detail' emp.manager.pk %}">{{ emp.manager.full_name }}</a>
        {% else %}—{% endif %}
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="4">No employees in this department.</td></tr>
    {% endfor %}
  </tbody>
</table>

<h2>Projects ({{ projects.count }})</h2>
<ul>
  {% for proj in projects %}
    <li>
      <a href="{% url 'hrms:project_detail' proj.pk %}">{{ proj.name }}</a>
      — {{ proj.get_status_display }}
    </li>
  {% empty %}
    <li>None</li>
  {% endfor %}
</ul>
{% endblock %}
```

#### `hrms/templates/hrms/department_form.html`

```html
{% extends "hrms/base.html" %}
{% block title %}{{ action }} Department{% endblock %}
{% block content %}
<h1>{{ action }} Department</h1>

<div id="form-result"></div>

<form
  hx-post="{% if object %}{% url 'hrms:department_update' object.pk %}{% else %}{% url 'hrms:department_create' %}{% endif %}"
  hx-target="#form-result"
  hx-swap="innerHTML"
>
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">{{ action }}</button>
  <a href="{% url 'hrms:department_list' %}">Cancel</a>
</form>
{% endblock %}
```

#### `hrms/templates/hrms/department_confirm_delete.html`

```html
{% extends "hrms/base.html" %}
{% block title %}Delete Department{% endblock %}
{% block content %}
<h1>Delete Department: {{ object }}</h1>
<p>Are you sure? Sub-departments will be unlinked and employees will lose their department reference.</p>

<div id="delete-result"></div>

<button
  hx-post="{% url 'hrms:department_delete' object.pk %}"
  hx-target="#delete-result"
  hx-swap="innerHTML"
>Yes, Delete</button>
<a href="{% url 'hrms:department_list' %}">Cancel</a>
{% endblock %}
```

---

### Employee Templates

#### `hrms/templates/hrms/employee_list.html`

```html
{% extends "hrms/base.html" %}
{% block title %}Employees{% endblock %}
{% block content %}
<h1>Employees</h1>

<a href="{% url 'hrms:employee_create' %}">+ New Employee</a>

<form>
  <input
    type="text"
    name="q"
    value="{{ q }}"
    placeholder="Search name or email…"
    hx-get="{% url 'hrms:employee_list' %}"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#employee-rows"
    hx-swap="innerHTML"
    hx-include="[name='level'],[name='dept']"
  >

  <select
    name="level"
    hx-get="{% url 'hrms:employee_list' %}"
    hx-trigger="change"
    hx-target="#employee-rows"
    hx-swap="innerHTML"
    hx-include="[name='q'],[name='dept']"
  >
    <option value="">All Levels</option>
    {% for val, label in level_choices %}
      <option value="{{ val }}" {% if val == level %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>

  <select
    name="dept"
    hx-get="{% url 'hrms:employee_list' %}"
    hx-trigger="change"
    hx-target="#employee-rows"
    hx-swap="innerHTML"
    hx-include="[name='q'],[name='level']"
  >
    <option value="">All Departments</option>
    {% for dept in departments %}
      <option value="{{ dept.pk }}" {% if dept.pk|stringformat:"s" == dept_id %}selected{% endif %}>
        {{ dept.name }}
      </option>
    {% endfor %}
  </select>
</form>

<table border="1">
  <thead>
    <tr>
      <th>Name</th><th>Title</th><th>Level</th><th>Department</th><th>Manager</th><th>Actions</th>
    </tr>
  </thead>
  <tbody id="employee-rows">
    {% include "hrms/employees/_table_rows.html" %}
  </tbody>
</table>
{% endblock %}
```

#### `hrms/templates/hrms/employees/_table_rows.html`

```html
{% for emp in employees %}
<tr>
  <td><a href="{% url 'hrms:employee_detail' emp.pk %}">{{ emp.full_name }}</a></td>
  <td>{{ emp.title }}</td>
  <td>{{ emp.get_level_display }}</td>
  <td>{{ emp.department }}</td>
  <td>
    {% if emp.manager %}
      <a href="{% url 'hrms:employee_detail' emp.manager.pk %}">{{ emp.manager.full_name }}</a>
    {% else %}—{% endif %}
  </td>
  <td>
    <a href="{% url 'hrms:employee_update' emp.pk %}">Edit</a> |
    <button
      hx-delete="{% url 'hrms:employee_delete' emp.pk %}"
      hx-target="closest tr"
      hx-swap="outerHTML"
      hx-confirm="Delete {{ emp.full_name }}?"
    >Delete</button>
  </td>
</tr>
{% empty %}
<tr><td colspan="6">No employees found.</td></tr>
{% endfor %}
```

#### `hrms/templates/hrms/employee_detail.html`

```html
{% extends "hrms/base.html" %}
{% block title %}{{ emp.full_name }}{% endblock %}
{% block content %}
<h1>{{ emp.full_name }}</h1>

<p>Title: {{ emp.title }}</p>
<p>Level: {{ emp.get_level_display }}</p>
<p>Type: {{ emp.get_employee_type_display }}</p>
<p>Department:
  {% if emp.department %}
    <a href="{% url 'hrms:department_detail' emp.department.pk %}">{{ emp.department }}</a>
  {% else %}—{% endif %}
</p>
<p>Manager:
  {% if emp.manager %}
    <a href="{% url 'hrms:employee_detail' emp.manager.pk %}">{{ emp.manager.full_name }}</a>
  {% else %}(none — top of hierarchy){% endif %}
</p>
<p>Hire Date: {{ emp.hire_date }}</p>
<p>Active: {{ emp.is_active|yesno:"Yes,No" }}</p>
<p>Bio: {{ emp.bio }}</p>

<p>
  <a href="{% url 'hrms:employee_update' emp.pk %}">Edit</a> |
  <button
    hx-delete="{% url 'hrms:employee_delete' emp.pk %}"
    hx-target="#delete-result"
    hx-swap="innerHTML"
    hx-confirm="Permanently delete {{ emp.full_name }}?"
  >Delete</button>
</p>
<div id="delete-result"></div>

<h2>Direct Reports ({{ direct_reports.count }})</h2>
<ul>
  {% for dr in direct_reports %}
    <li><a href="{% url 'hrms:employee_detail' dr.pk %}">{{ dr.full_name }}</a> — {{ dr.title }}</li>
  {% empty %}
    <li>None</li>
  {% endfor %}
</ul>

<h2>Projects (member)</h2>
<ul>
  {% for proj in projects %}
    <li><a href="{% url 'hrms:project_detail' proj.pk %}">{{ proj.name }}</a></li>
  {% empty %}
    <li>None</li>
  {% endfor %}
</ul>

<h2>Led Projects</h2>
<ul>
  {% for proj in led_projects %}
    <li><a href="{% url 'hrms:project_detail' proj.pk %}">{{ proj.name }}</a></li>
  {% empty %}
    <li>None</li>
  {% endfor %}
</ul>
{% endblock %}
```

#### `hrms/templates/hrms/employee_form.html`

```html
{% extends "hrms/base.html" %}
{% block title %}{{ action }} Employee{% endblock %}
{% block content %}
<h1>{{ action }} Employee</h1>

<div id="form-result"></div>

<form
  hx-post="{% if object %}{% url 'hrms:employee_update' object.pk %}{% else %}{% url 'hrms:employee_create' %}{% endif %}"
  hx-target="#form-result"
  hx-swap="innerHTML"
>
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">{{ action }}</button>
  <a href="{% url 'hrms:employee_list' %}">Cancel</a>
</form>
{% endblock %}
```

#### `hrms/templates/hrms/employee_confirm_delete.html`

```html
{% extends "hrms/base.html" %}
{% block title %}Delete Employee{% endblock %}
{% block content %}
<h1>Delete Employee: {{ object }}</h1>
<p>Are you sure? This action cannot be undone.</p>

<div id="delete-result"></div>

<button
  hx-post="{% url 'hrms:employee_delete' object.pk %}"
  hx-target="#delete-result"
  hx-swap="innerHTML"
>Yes, Delete</button>
<a href="{% url 'hrms:employee_list' %}">Cancel</a>
{% endblock %}
```

---

### Project Templates

#### `hrms/templates/hrms/project_list.html`

```html
{% extends "hrms/base.html" %}
{% block title %}Projects{% endblock %}
{% block content %}
<h1>Projects</h1>

<a href="{% url 'hrms:project_create' %}">+ New Project</a>

<form>
  <input
    type="text"
    name="q"
    value="{{ q }}"
    placeholder="Search projects…"
    hx-get="{% url 'hrms:project_list' %}"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#project-rows"
    hx-swap="innerHTML"
    hx-include="[name='status']"
  >

  <select
    name="status"
    hx-get="{% url 'hrms:project_list' %}"
    hx-trigger="change"
    hx-target="#project-rows"
    hx-swap="innerHTML"
    hx-include="[name='q']"
  >
    <option value="">All Statuses</option>
    {% for val, label in status_choices %}
      <option value="{{ val }}" {% if val == status %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>
</form>

<table border="1">
  <thead>
    <tr>
      <th>Name</th><th>Status</th><th>Department</th>
      <th>Lead</th><th>Members</th><th>Start</th><th>End</th><th>Actions</th>
    </tr>
  </thead>
  <tbody id="project-rows">
    {% include "hrms/projects/_table_rows.html" %}
  </tbody>
</table>
{% endblock %}
```

#### `hrms/templates/hrms/projects/_table_rows.html`

```html
{% for project in projects %}
<tr>
  <td><a href="{% url 'hrms:project_detail' project.pk %}">{{ project.name }}</a></td>
  <td>{{ project.get_status_display }}</td>
  <td>
    {% if project.department %}
      <a href="{% url 'hrms:department_detail' project.department.pk %}">{{ project.department.name }}</a>
    {% else %}—{% endif %}
  </td>
  <td>
    {% if project.lead %}
      <a href="{% url 'hrms:employee_detail' project.lead.pk %}">{{ project.lead.full_name }}</a>
    {% else %}—{% endif %}
  </td>
  <td>{{ project.members.count }}</td>
  <td>{{ project.start_date|default:"—" }}</td>
  <td>{{ project.end_date|default:"—" }}</td>
  <td>
    <a href="{% url 'hrms:project_update' project.pk %}">Edit</a> |
    <button
      hx-delete="{% url 'hrms:project_delete' project.pk %}"
      hx-target="closest tr"
      hx-swap="outerHTML"
      hx-confirm="Delete project {{ project.name }}?"
    >Delete</button>
  </td>
</tr>
{% empty %}
<tr><td colspan="8">No projects found.</td></tr>
{% endfor %}
```

#### `hrms/templates/hrms/project_detail.html`

```html
{% extends "hrms/base.html" %}
{% block title %}{{ project.name }}{% endblock %}
{% block content %}
<h1>{{ project.name }}</h1>

<p>Status: {{ project.get_status_display }}</p>
<p>Department:
  {% if project.department %}
    <a href="{% url 'hrms:department_detail' project.department.pk %}">{{ project.department.name }}</a>
  {% else %}—{% endif %}
</p>
<p>Lead:
  {% if project.lead %}
    <a href="{% url 'hrms:employee_detail' project.lead.pk %}">{{ project.lead.full_name }}</a>
  {% else %}—{% endif %}
</p>
<p>Start Date: {{ project.start_date|default:"Not set" }}</p>
<p>End Date: {{ project.end_date|default:"Not set" }}</p>
<p>Description: {{ project.description }}</p>

<p>
  <a href="{% url 'hrms:project_update' project.pk %}">Edit</a> |
  <button
    hx-delete="{% url 'hrms:project_delete' project.pk %}"
    hx-target="#delete-result"
    hx-swap="innerHTML"
    hx-confirm="Permanently delete {{ project.name }}?"
  >Delete</button>
</p>
<div id="delete-result"></div>

<h2>Members ({{ members.count }})</h2>
<table border="1">
  <thead>
    <tr><th>Name</th><th>Title</th><th>Level</th><th>Department</th></tr>
  </thead>
  <tbody>
    {% for member in members %}
    <tr>
      <td><a href="{% url 'hrms:employee_detail' member.pk %}">{{ member.full_name }}</a></td>
      <td>{{ member.title }}</td>
      <td>{{ member.get_level_display }}</td>
      <td>
        {% if member.department %}
          <a href="{% url 'hrms:department_detail' member.department.pk %}">{{ member.department.name }}</a>
        {% else %}—{% endif %}
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="4">No members assigned.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

#### `hrms/templates/hrms/project_form.html`

```html
{% extends "hrms/base.html" %}
{% block title %}{{ action }} Project{% endblock %}
{% block content %}
<h1>{{ action }} Project</h1>

<div id="form-result"></div>

<form
  hx-post="{% if object %}{% url 'hrms:project_update' object.pk %}{% else %}{% url 'hrms:project_create' %}{% endif %}"
  hx-target="#form-result"
  hx-swap="innerHTML"
>
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">{{ action }}</button>
  <a href="{% url 'hrms:project_list' %}">Cancel</a>
</form>
{% endblock %}
```

#### `hrms/templates/hrms/project_confirm_delete.html`

```html
{% extends "hrms/base.html" %}
{% block title %}Delete Project{% endblock %}
{% block content %}
<h1>Delete Project: {{ object }}</h1>
<p>Are you sure? This will remove the project and all its member assignments permanently.</p>

<div id="delete-result"></div>

<button
  hx-post="{% url 'hrms:project_delete' object.pk %}"
  hx-target="#delete-result"
  hx-swap="innerHTML"
>Yes, Delete</button>
<a href="{% url 'hrms:project_list' %}">Cancel</a>
{% endblock %}
```

---

## 11. HTMX & CSRF Setup

### How CSRF Works Here

Django requires a CSRF token on all non-GET requests. The `hx-headers` attribute on `<body>` injects it globally:

```html
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
```

Every HTMX request inherits this header, so `CsrfViewMiddleware` is satisfied for all HTMX mutations with zero per-element configuration. The `{% csrf_token %}` tag inside `<form>` elements remains for non-JS fallback only.

### HTMX Patterns Used

| Pattern | Usage |
|---|---|
| `hx-get` + `hx-trigger="keyup delay:300ms"` | Live search, returns partial `_table_rows.html` |
| `hx-post` + `hx-target="#form-result"` | Inline form submission confirmation |
| `hx-delete` + `hx-target="closest tr"` + `hx-swap="outerHTML"` | Remove a row without page reload |
| `hx-confirm` | Native browser dialog before destructive actions |
| `hx-include` | Carry sibling filter inputs in a filtered search request |

### How HTMX Partials Work with CBVs

The list views override `render_to_response` to detect the `HX-Request` header and return the `_table_rows.html` partial instead of the full page template. This keeps all filtering logic in one place (`get_queryset`) regardless of whether the request is a full page load or an HTMX swap:

```python
def render_to_response(self, context, **response_kwargs):
    if self.request.headers.get("HX-Request"):
        from django.template.response import TemplateResponse
        return TemplateResponse(self.request, "hrms/employees/_table_rows.html", context)
    return super().render_to_response(context, **response_kwargs)
```

### Django Settings — Ensure CSRF Middleware is Active

```python
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",   # ← required
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

---

## 12. Running the Project

```bash
# 1. Apply migrations
python manage.py migrate

# 2. Seed fake data
python seed_data.py

# 3. (Optional) Create a superuser for Django admin
python manage.py createsuperuser

# 4. (Optional) Register models in hrms/admin.py
```

```python
# hrms/admin.py
from django.contrib import admin
from .models import Department, Employee, Project

admin.site.register(Department)
admin.site.register(Employee)
admin.site.register(Project)
```

```bash
# 5. Start the dev server
python manage.py runserver
```

Open `http://127.0.0.1:8000/` to see the dashboard.

---

## What Changed vs. the Function-Based Version

| Area | Function-based | Class-based |
|---|---|---|
| `views.py` | One function per operation | One class per operation, inheriting a generic base |
| HTMX detection | `if request.headers.get("HX-Request")` inline | Isolated in `HtmxResponseMixin.is_htmx()` and `render_to_response()` |
| Redirect after save | `return redirect(...)` | `get_absolute_url()` on the model; CBV calls it automatically |
| Template names | Custom paths (`employees/list.html`) | CBV convention (`employee_list.html`) — no `template_name` needed |
| `urls.py` | `path(..., views.employee_list)` | `path(..., views.EmployeeListView.as_view())` |
| Queryset filtering | Inside the function body | In `get_queryset()` override |
| Extra context | Passed as dict to `render()` | Added in `get_context_data()` override |
| Models | Identical | `get_absolute_url()` added to each model |
| Forms | Identical | Identical |
| Seed script | Identical | Identical |

---

## Architecture Overview

```
Alphabet Inc. Hierarchy
═══════════════════════

CEO (Sundar Pichai)
 ├── CFO
 ├── CTO
 └── SVP, Google Search
      └── Director, Search Quality
           ├── Group Manager
           │    ├── L4 Staff SWE
           │    ├── L3 Senior SWE
           │    └── L2 SWE
           └── Senior PM
                └── L1 Associate SWE

Department Tree
═══════════════
Google Cloud (top-level)
 ├── GKE & Compute        (sub-dept, parent=Google Cloud)
 ├── BigQuery & Analytics (sub-dept)
 └── Cloud Security       (sub-dept)

Project Relationships
═════════════════════
Project "Gemini Ultra Rollout"
 ├── department  → AI Research (DeepMind)
 ├── lead        → Employee (Group Manager)
 └── members     → [Employee, Employee, Employee, …]
```

---

*End of guide. The application is intentionally unstyled to keep focus on Django CBV design, HTMX integration patterns, and the CSRF header approach.*
