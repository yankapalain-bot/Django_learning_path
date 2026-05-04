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