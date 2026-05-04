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

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
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