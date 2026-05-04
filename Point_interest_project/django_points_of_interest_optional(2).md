# Django Points of Interest App
### A Student Guide to Primary Keys, Foreign Keys & SQL Joins

---

## Overview

This tutorial walks you through building a **Points of Interest (POI)** Django web application. The app demonstrates:

- **Primary Keys (PK)** — unique identifiers for every record
- **Foreign Keys (FK)** — how models reference each other
- **SQL JOINs** — surfaced through Django ORM relationships and dropdown-driven queries
- **CRUD operations** — Create, Read, Update, Delete for all POI types

---

## 1. Project Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install django

# Create project and app
django-admin startproject poi_project
cd poi_project
python manage.py startapp poi
```

Register the app in `poi_project/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'poi',
]
```

---

## 2. Database Design & Conceptual Model

Before writing any code, understand the entity relationships:

```
City (PK: id)
 └── Neighbourhood (PK: id, FK → City)
      └── PointOfInterest [abstract base] (PK: id, FK → Neighbourhood)
           ├── Restaurant (PK: id, FK → PointOfInterest, FK → Cuisine)
           ├── Museum     (PK: id, FK → PointOfInterest, FK → Theme)
           ├── Government (PK: id, FK → PointOfInterest)
           └── Bank       (PK: id, FK → PointOfInterest)

Cuisine  (PK: id)  ← shared by Restaurants
Theme    (PK: id)  ← shared by Museums
```

### Why These Relationships?

| Relationship | Type | Purpose (JOIN equivalent) |
|---|---|---|
| Neighbourhood → City | Many-to-One | `SELECT * FROM neighbourhood JOIN city ON city_id = city.id` |
| POI → Neighbourhood | Many-to-One | `SELECT * FROM poi JOIN neighbourhood ON neighbourhood_id = neighbourhood.id` |
| Restaurant → Cuisine | Many-to-One | `SELECT * FROM restaurant JOIN cuisine ON cuisine_id = cuisine.id` |
| Museum → Theme | Many-to-One | `SELECT * FROM museum JOIN theme ON theme_id = theme.id` |
| Restaurant ↔ Museum | Many-to-Many (via `NearbyPOI`) | Shows cross-category JOINs |

---

## 3. Models (`poi/models.py`)

```python
from django.db import models


# ─────────────────────────────────────────
# LOOKUP / REFERENCE TABLES
# These act as JOIN targets — their PKs are
# referenced as FKs in the main POI models.
# ─────────────────────────────────────────

class City(models.Model):
    """
    PK: id (auto)
    Referenced by: Neighbourhood.city (FK)
    """
    name    = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Cities"

    def __str__(self):
        return f"{self.name}, {self.country}"


class Neighbourhood(models.Model):
    """
    PK: id (auto)
    FK → City         (JOIN: neighbourhood ⟶ city)
    Referenced by: PointOfInterest.neighbourhood (FK)
    """
    name = models.CharField(max_length=100)
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='neighbourhoods'
    )

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class Cuisine(models.Model):
    """
    PK: id (auto)
    Referenced by: Restaurant.cuisine (FK)
    JOIN: restaurant ⟶ cuisine
    """
    name        = models.CharField(max_length=100)   # e.g. Italian, Japanese
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class MuseumTheme(models.Model):
    """
    PK: id (auto)
    Referenced by: Museum.theme (FK)
    JOIN: museum ⟶ museum_theme
    """
    name        = models.CharField(max_length=100)  # e.g. Natural History, Science
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# BASE POINT OF INTEREST
# Every specific POI type (Restaurant, Museum,
# etc.) has a OneToOne link to this model.
# This allows a shared PK space and lets SQL
# JOIN all POI types through one table.
# ─────────────────────────────────────────

class PointOfInterest(models.Model):
    """
    PK: id (auto)
    FK → Neighbourhood
    This is the central JOIN hub:
      SELECT * FROM poi JOIN neighbourhood ON neighbourhood_id = neighbourhood.id
                        JOIN city          ON city_id = city.id
    """
    POI_TYPES = [
        ('restaurant', 'Restaurant'),
        ('museum',     'Museum'),
        ('government', 'Government'),
        ('bank',       'Bank'),
    ]

    name          = models.CharField(max_length=200)
    latitude      = models.DecimalField(max_digits=9, decimal_places=6)
    longitude     = models.DecimalField(max_digits=9, decimal_places=6)
    address       = models.CharField(max_length=300, blank=True)
    phone         = models.CharField(max_length=30,  blank=True)
    website       = models.URLField(blank=True)
    poi_type      = models.CharField(max_length=20, choices=POI_TYPES)
    neighbourhood = models.ForeignKey(
        Neighbourhood,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='points_of_interest'
    )
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Point of Interest"
        verbose_name_plural = "Points of Interest"

    def __str__(self):
        return f"{self.name} [{self.poi_type}]"


# ─────────────────────────────────────────
# SPECIFIC POI TYPES
# Each uses a OneToOneField to PointOfInterest.
# OneToOne means: same PK, automatic JOIN.
# SQL: SELECT * FROM restaurant
#        JOIN pointofinterest ON poi_id = pointofinterest.id
# ─────────────────────────────────────────

class Restaurant(models.Model):
    """
    PK: id (auto)
    OneToOne → PointOfInterest  (shares the POI's identity)
    FK → Cuisine                (JOIN to lookup table)
    """
    poi = models.OneToOneField(
        PointOfInterest,
        on_delete=models.CASCADE,
        related_name='restaurant'
    )
    cuisine         = models.ForeignKey(
        Cuisine,
        on_delete=models.SET_NULL,
        null=True,
        related_name='restaurants'
    )
    seating_capacity = models.PositiveIntegerField(default=0)
    price_range      = models.CharField(
        max_length=10,
        choices=[('$','$'), ('$$','$$'), ('$$$','$$$'), ('$$$$','$$$$')],
        default='$$'
    )
    has_delivery     = models.BooleanField(default=False)
    has_takeout      = models.BooleanField(default=False)
    michelin_stars   = models.PositiveSmallIntegerField(default=0)
    opening_hours    = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.poi.name} — {self.cuisine}"


class Museum(models.Model):
    """
    PK: id (auto)
    OneToOne → PointOfInterest
    FK → MuseumTheme
    """
    poi = models.OneToOneField(
        PointOfInterest,
        on_delete=models.CASCADE,
        related_name='museum'
    )
    theme              = models.ForeignKey(
        MuseumTheme,
        on_delete=models.SET_NULL,
        null=True,
        related_name='museums'
    )
    current_exhibition = models.CharField(max_length=300, blank=True)
    permanent_collection = models.TextField(blank=True)
    admission_fee      = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_free            = models.BooleanField(default=False)
    founding_year      = models.PositiveIntegerField(null=True, blank=True)
    num_floors         = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f"{self.poi.name} — {self.theme}"


class GovernmentOffice(models.Model):
    """
    PK: id (auto)
    OneToOne → PointOfInterest
    """
    LEVEL_CHOICES = [
        ('federal',   'Federal'),
        ('state',     'State / Provincial'),
        ('municipal', 'Municipal'),
    ]

    poi            = models.OneToOneField(
        PointOfInterest,
        on_delete=models.CASCADE,
        related_name='government'
    )
    department     = models.CharField(max_length=200)
    level          = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='municipal')
    official_name  = models.CharField(max_length=200, blank=True)
    services_offered = models.TextField(blank=True)
    appointment_required = models.BooleanField(default=False)
    public_access  = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.poi.name} — {self.department}"


class Bank(models.Model):
    """
    PK: id (auto)
    OneToOne → PointOfInterest
    """
    BANK_TYPES = [
        ('commercial', 'Commercial Bank'),
        ('credit_union', 'Credit Union'),
        ('investment',  'Investment Bank'),
        ('central',     'Central Bank'),
        ('savings',     'Savings Bank'),
    ]

    poi           = models.OneToOneField(
        PointOfInterest,
        on_delete=models.CASCADE,
        related_name='bank'
    )
    bank_name     = models.CharField(max_length=200)
    bank_type     = models.CharField(max_length=20, choices=BANK_TYPES, default='commercial')
    swift_code    = models.CharField(max_length=11, blank=True)
    has_atm       = models.BooleanField(default=True)
    num_atms      = models.PositiveSmallIntegerField(default=1)
    drive_through = models.BooleanField(default=False)
    accepts_foreign_currency = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.bank_name} — {self.poi.name}"


# ─────────────────────────────────────────
# MANY-TO-MANY CROSS-JOIN EXAMPLE
# Shows students how a junction table works:
#   SELECT poi_a.name, poi_b.name
#   FROM nearbypoi
#     JOIN pointofinterest poi_a ON from_poi_id = poi_a.id
#     JOIN pointofinterest poi_b ON to_poi_id   = poi_b.id
# ─────────────────────────────────────────

class NearbyPOI(models.Model):
    """
    Junction / bridge table.
    PK: id (auto)
    FK → PointOfInterest (from_poi)
    FK → PointOfInterest (to_poi)
    Represents: "from_poi is near to_poi, walkable in X minutes"
    """
    from_poi       = models.ForeignKey(
        PointOfInterest,
        on_delete=models.CASCADE,
        related_name='nearby_from'
    )
    to_poi         = models.ForeignKey(
        PointOfInterest,
        on_delete=models.CASCADE,
        related_name='nearby_to'
    )
    walk_minutes   = models.PositiveSmallIntegerField(default=5)

    class Meta:
        unique_together = ('from_poi', 'to_poi')
        verbose_name_plural = "Nearby POIs"

    def __str__(self):
        return f"{self.from_poi.name} → {self.to_poi.name} ({self.walk_minutes} min walk)"
```

---

## 4. Migrations

```bash
python manage.py makemigrations poi
python manage.py migrate
```

To inspect the SQL Django generates (great for teaching!):

```bash
python manage.py sqlmigrate poi 0001
```

---

## 5. Admin Registration (`poi/admin.py`)

```python
from django.contrib import admin
from .models import (
    City, Neighbourhood, Cuisine, MuseumTheme,
    PointOfInterest, Restaurant, Museum,
    GovernmentOffice, Bank, NearbyPOI
)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'country']
    search_fields = ['name']

@admin.register(Neighbourhood)
class NeighbourhoodAdmin(admin.ModelAdmin):
    list_display  = ['name', 'city']
    list_filter   = ['city']
    search_fields = ['name']

@admin.register(PointOfInterest)
class POIAdmin(admin.ModelAdmin):
    list_display  = ['name', 'poi_type', 'neighbourhood', 'latitude', 'longitude']
    list_filter   = ['poi_type', 'neighbourhood__city']
    search_fields = ['name', 'address']

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display  = ['poi', 'cuisine', 'price_range', 'michelin_stars', 'has_delivery']
    list_filter   = ['cuisine', 'price_range', 'michelin_stars']

@admin.register(Museum)
class MuseumAdmin(admin.ModelAdmin):
    list_display = ['poi', 'theme', 'current_exhibition', 'is_free', 'founding_year']
    list_filter  = ['theme', 'is_free']

@admin.register(GovernmentOffice)
class GovernmentAdmin(admin.ModelAdmin):
    list_display = ['poi', 'department', 'level', 'public_access']
    list_filter  = ['level']

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['poi', 'bank_name', 'bank_type', 'has_atm', 'drive_through']
    list_filter  = ['bank_type']

@admin.register(NearbyPOI)
class NearbyPOIAdmin(admin.ModelAdmin):
    list_display = ['from_poi', 'to_poi', 'walk_minutes']

admin.site.register(Cuisine)
admin.site.register(MuseumTheme)
```

---

## 6. URLs (`poi/urls.py` + project `urls.py`)

### `poi/urls.py`

```python
from django.urls import path
from . import views

app_name = 'poi'

urlpatterns = [
    # ── Dashboard / JOIN queries ──────────────────────────────
    path('',              views.dashboard,   name='dashboard'),
    path('join-query/',   views.join_query,  name='join_query'),

    # ── Points of Interest (generic list) ────────────────────
    path('poi/',          views.poi_list,    name='poi_list'),
    path('poi/create/',   views.poi_create,  name='poi_create'),
    path('poi/<int:pk>/', views.poi_detail,  name='poi_detail'),
    path('poi/<int:pk>/edit/',   views.poi_edit,   name='poi_edit'),
    path('poi/<int:pk>/delete/', views.poi_delete, name='poi_delete'),

    # ── Restaurants ───────────────────────────────────────────
    path('restaurants/',                    views.restaurant_list,   name='restaurant_list'),
    path('restaurants/create/',             views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/edit/',      views.restaurant_edit,   name='restaurant_edit'),
    path('restaurants/<int:pk>/delete/',    views.restaurant_delete, name='restaurant_delete'),

    # ── Museums ───────────────────────────────────────────────
    path('museums/',                    views.museum_list,   name='museum_list'),
    path('museums/create/',             views.museum_create, name='museum_create'),
    path('museums/<int:pk>/edit/',      views.museum_edit,   name='museum_edit'),
    path('museums/<int:pk>/delete/',    views.museum_delete, name='museum_delete'),

    # ── Government Offices ────────────────────────────────────
    path('government/',                 views.government_list,   name='government_list'),
    path('government/create/',          views.government_create, name='government_create'),
    path('government/<int:pk>/edit/',   views.government_edit,   name='government_edit'),
    path('government/<int:pk>/delete/', views.government_delete, name='government_delete'),

    # ── Banks ─────────────────────────────────────────────────
    path('banks/',                    views.bank_list,   name='bank_list'),
    path('banks/create/',             views.bank_create, name='bank_create'),
    path('banks/<int:pk>/edit/',      views.bank_edit,   name='bank_edit'),
    path('banks/<int:pk>/delete/',    views.bank_delete, name='bank_delete'),
]
```

### `poi_project/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',       include('poi.urls', namespace='poi')),
]
```

---

## 7. Forms (`poi/forms.py`)

```python
from django import forms
from .models import (
    PointOfInterest, Restaurant, Museum,
    GovernmentOffice, Bank,
    City, Neighbourhood, Cuisine, MuseumTheme
)


class POIForm(forms.ModelForm):
    class Meta:
        model  = PointOfInterest
        fields = ['name', 'latitude', 'longitude', 'address',
                  'phone', 'website', 'poi_type', 'neighbourhood']
        widgets = {
            'neighbourhood': forms.Select(attrs={'class': 'form-select'}),
            'poi_type':      forms.Select(attrs={'class': 'form-select'}),
        }


class RestaurantForm(forms.ModelForm):
    class Meta:
        model  = Restaurant
        fields = ['cuisine', 'seating_capacity', 'price_range',
                  'has_delivery', 'has_takeout', 'michelin_stars', 'opening_hours']
        widgets = {
            'cuisine':     forms.Select(attrs={'class': 'form-select'}),
            'price_range': forms.Select(attrs={'class': 'form-select'}),
        }


class MuseumForm(forms.ModelForm):
    class Meta:
        model  = Museum
        fields = ['theme', 'current_exhibition', 'permanent_collection',
                  'admission_fee', 'is_free', 'founding_year', 'num_floors']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
        }


class GovernmentForm(forms.ModelForm):
    class Meta:
        model  = GovernmentOffice
        fields = ['department', 'level', 'official_name',
                  'services_offered', 'appointment_required', 'public_access']
        widgets = {
            'level': forms.Select(attrs={'class': 'form-select'}),
        }


class BankForm(forms.ModelForm):
    class Meta:
        model  = Bank
        fields = ['bank_name', 'bank_type', 'swift_code',
                  'has_atm', 'num_atms', 'drive_through', 'accepts_foreign_currency']
        widgets = {
            'bank_type': forms.Select(attrs={'class': 'form-select'}),
        }


# ── JOIN Query Form (drives the dropdown UI) ──────────────────
class JoinQueryForm(forms.Form):
    JOIN_CHOICES = [
        ('poi_by_city',          '① All POIs in a City  [POI ⟶ Neighbourhood ⟶ City]'),
        ('restaurants_by_cuisine','② Restaurants by Cuisine  [Restaurant ⟶ Cuisine]'),
        ('museums_by_theme',     '③ Museums by Theme  [Museum ⟶ MuseumTheme]'),
        ('banks_with_atm',       '④ Banks with ATMs in a Neighbourhood  [Bank ⟶ POI ⟶ Neighbourhood]'),
        ('nearby_pois',          '⑤ Nearby POIs (cross-type)  [NearbyPOI ⟶ POI × 2]'),
        ('free_museums_by_city', '⑥ Free Museums by City  [Museum ⟶ POI ⟶ Neighbourhood ⟶ City]'),
        ('govt_by_level',        '⑦ Government Offices by Level  [GovernmentOffice ⟶ POI]'),
    ]

    query_type    = forms.ChoiceField(
        choices=JOIN_CHOICES,
        label='Select JOIN Query',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    filter_city   = forms.ModelChoiceField(
        queryset=City.objects.all(),
        required=False,
        empty_label='— Any City —',
        label='City',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    filter_neighbourhood = forms.ModelChoiceField(
        queryset=Neighbourhood.objects.select_related('city').all(),
        required=False,
        empty_label='— Any Neighbourhood —',
        label='Neighbourhood',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    filter_cuisine = forms.ModelChoiceField(
        queryset=Cuisine.objects.all(),
        required=False,
        empty_label='— Any Cuisine —',
        label='Cuisine',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    filter_theme  = forms.ModelChoiceField(
        queryset=MuseumTheme.objects.all(),
        required=False,
        empty_label='— Any Theme —',
        label='Museum Theme',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    filter_govt_level = forms.ChoiceField(
        choices=[('', '— Any Level —')] + GovernmentOffice.LEVEL_CHOICES,
        required=False,
        label='Government Level',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
```

---

## 8. Views (`poi/views.py`)

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import (
    PointOfInterest, Restaurant, Museum,
    GovernmentOffice, Bank, NearbyPOI,
    City, Neighbourhood, Cuisine, MuseumTheme
)
from .forms import (
    POIForm, RestaurantForm, MuseumForm,
    GovernmentForm, BankForm, JoinQueryForm
)


# ════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════

def dashboard(request):
    context = {
        'total_poi':         PointOfInterest.objects.count(),
        'total_restaurants': Restaurant.objects.count(),
        'total_museums':     Museum.objects.count(),
        'total_govt':        GovernmentOffice.objects.count(),
        'total_banks':       Bank.objects.count(),
        'cities':            City.objects.all(),
    }
    return render(request, 'poi/dashboard.html', context)


# ════════════════════════════════════════════
#  JOIN QUERY VIEW
#  This is the core teaching view.
#  A dropdown selects the join type; results
#  are displayed in a table.
# ════════════════════════════════════════════

def join_query(request):
    form    = JoinQueryForm(request.GET or None)
    results = []
    columns = []
    sql_explanation = ''

    if form.is_valid():
        qt         = form.cleaned_data['query_type']
        city       = form.cleaned_data.get('filter_city')
        nbhood     = form.cleaned_data.get('filter_neighbourhood')
        cuisine    = form.cleaned_data.get('filter_cuisine')
        theme      = form.cleaned_data.get('filter_theme')
        govt_level = form.cleaned_data.get('filter_govt_level')

        # ① POI → Neighbourhood → City
        if qt == 'poi_by_city':
            qs = PointOfInterest.objects.select_related(
                'neighbourhood', 'neighbourhood__city'
            )
            if city:
                qs = qs.filter(neighbourhood__city=city)
            columns = ['POI Name', 'Type', 'Neighbourhood', 'City', 'Latitude', 'Longitude']
            results = [
                [p.name, p.get_poi_type_display(),
                 p.neighbourhood.name if p.neighbourhood else '—',
                 p.neighbourhood.city.name if p.neighbourhood else '—',
                 p.latitude, p.longitude]
                for p in qs
            ]
            sql_explanation = (
                "SELECT poi.name, poi.poi_type, n.name AS neighbourhood, c.name AS city,\n"
                "       poi.latitude, poi.longitude\n"
                "FROM poi_pointofinterest poi\n"
                "  INNER JOIN poi_neighbourhood n ON poi.neighbourhood_id = n.id\n"
                "  INNER JOIN poi_city          c ON n.city_id = c.id\n"
                + (f"WHERE c.id = {city.pk};" if city else ";")
            )

        # ② Restaurant → Cuisine
        elif qt == 'restaurants_by_cuisine':
            qs = Restaurant.objects.select_related('poi', 'cuisine')
            if cuisine:
                qs = qs.filter(cuisine=cuisine)
            columns = ['Restaurant', 'Cuisine', 'Price', 'Michelin ★', 'Delivery', 'Takeout']
            results = [
                [r.poi.name, str(r.cuisine), r.price_range,
                 '★' * r.michelin_stars if r.michelin_stars else '—',
                 '✓' if r.has_delivery else '✗',
                 '✓' if r.has_takeout else '✗']
                for r in qs
            ]
            sql_explanation = (
                "SELECT poi.name, c.name AS cuisine, r.price_range,\n"
                "       r.michelin_stars, r.has_delivery, r.has_takeout\n"
                "FROM poi_restaurant r\n"
                "  INNER JOIN poi_pointofinterest poi ON r.poi_id = poi.id\n"
                "  INNER JOIN poi_cuisine         c   ON r.cuisine_id = c.id\n"
                + (f"WHERE c.id = {cuisine.pk};" if cuisine else ";")
            )

        # ③ Museum → MuseumTheme
        elif qt == 'museums_by_theme':
            qs = Museum.objects.select_related('poi', 'theme')
            if theme:
                qs = qs.filter(theme=theme)
            columns = ['Museum', 'Theme', 'Exhibition', 'Free?', 'Admission', 'Founded']
            results = [
                [m.poi.name, str(m.theme), m.current_exhibition or '—',
                 '✓' if m.is_free else '✗',
                 f"${m.admission_fee}" if not m.is_free else 'Free',
                 m.founding_year or '—']
                for m in qs
            ]
            sql_explanation = (
                "SELECT poi.name, t.name AS theme, m.current_exhibition,\n"
                "       m.is_free, m.admission_fee, m.founding_year\n"
                "FROM poi_museum m\n"
                "  INNER JOIN poi_pointofinterest poi ON m.poi_id = poi.id\n"
                "  INNER JOIN poi_museumtheme     t   ON m.theme_id = t.id\n"
                + (f"WHERE t.id = {theme.pk};" if theme else ";")
            )

        # ④ Bank → POI → Neighbourhood (ATMs)
        elif qt == 'banks_with_atm':
            qs = Bank.objects.select_related(
                'poi', 'poi__neighbourhood', 'poi__neighbourhood__city'
            ).filter(has_atm=True)
            if nbhood:
                qs = qs.filter(poi__neighbourhood=nbhood)
            columns = ['Bank Name', 'Type', '# ATMs', 'Drive-Through', 'Neighbourhood', 'City']
            results = [
                [b.bank_name, b.get_bank_type_display(), b.num_atms,
                 '✓' if b.drive_through else '✗',
                 b.poi.neighbourhood.name if b.poi.neighbourhood else '—',
                 b.poi.neighbourhood.city.name if b.poi.neighbourhood else '—']
                for b in qs
            ]
            sql_explanation = (
                "SELECT b.bank_name, b.bank_type, b.num_atms, b.drive_through,\n"
                "       n.name AS neighbourhood, c.name AS city\n"
                "FROM poi_bank b\n"
                "  INNER JOIN poi_pointofinterest poi ON b.poi_id = poi.id\n"
                "  INNER JOIN poi_neighbourhood   n   ON poi.neighbourhood_id = n.id\n"
                "  INNER JOIN poi_city            c   ON n.city_id = c.id\n"
                "WHERE b.has_atm = TRUE\n"
                + (f"  AND n.id = {nbhood.pk};" if nbhood else ";")
            )

        # ⑤ NearbyPOI (many-to-many cross-join)
        elif qt == 'nearby_pois':
            qs = NearbyPOI.objects.select_related(
                'from_poi', 'to_poi',
                'from_poi__neighbourhood', 'to_poi__neighbourhood'
            )
            columns = ['From POI', 'Type', 'To POI', 'Type', 'Walk (min)']
            results = [
                [n.from_poi.name, n.from_poi.get_poi_type_display(),
                 n.to_poi.name,   n.to_poi.get_poi_type_display(),
                 n.walk_minutes]
                for n in qs
            ]
            sql_explanation = (
                "SELECT a.name AS from_poi, a.poi_type,\n"
                "       b.name AS to_poi,   b.poi_type,\n"
                "       np.walk_minutes\n"
                "FROM poi_nearbypoi np\n"
                "  INNER JOIN poi_pointofinterest a ON np.from_poi_id = a.id\n"
                "  INNER JOIN poi_pointofinterest b ON np.to_poi_id   = b.id;"
            )

        # ⑥ Free Museums → City (3-level join)
        elif qt == 'free_museums_by_city':
            qs = Museum.objects.select_related(
                'poi', 'poi__neighbourhood', 'poi__neighbourhood__city', 'theme'
            ).filter(is_free=True)
            if city:
                qs = qs.filter(poi__neighbourhood__city=city)
            columns = ['Museum', 'Theme', 'Exhibition', 'Neighbourhood', 'City']
            results = [
                [m.poi.name, str(m.theme), m.current_exhibition or '—',
                 m.poi.neighbourhood.name if m.poi.neighbourhood else '—',
                 m.poi.neighbourhood.city.name if m.poi.neighbourhood else '—']
                for m in qs
            ]
            sql_explanation = (
                "SELECT poi.name, t.name AS theme, m.current_exhibition,\n"
                "       n.name AS neighbourhood, c.name AS city\n"
                "FROM poi_museum m\n"
                "  INNER JOIN poi_pointofinterest poi ON m.poi_id = poi.id\n"
                "  INNER JOIN poi_museumtheme     t   ON m.theme_id = t.id\n"
                "  INNER JOIN poi_neighbourhood   n   ON poi.neighbourhood_id = n.id\n"
                "  INNER JOIN poi_city            c   ON n.city_id = c.id\n"
                "WHERE m.is_free = TRUE\n"
                + (f"  AND c.id = {city.pk};" if city else ";")
            )

        # ⑦ Government Offices by Level
        elif qt == 'govt_by_level':
            qs = GovernmentOffice.objects.select_related(
                'poi', 'poi__neighbourhood', 'poi__neighbourhood__city'
            )
            if govt_level:
                qs = qs.filter(level=govt_level)
            columns = ['Office Name', 'Department', 'Level', 'Public Access', 'Neighbourhood', 'City']
            results = [
                [g.poi.name, g.department, g.get_level_display(),
                 '✓' if g.public_access else '✗',
                 g.poi.neighbourhood.name if g.poi.neighbourhood else '—',
                 g.poi.neighbourhood.city.name if g.poi.neighbourhood else '—']
                for g in qs
            ]
            sql_explanation = (
                "SELECT poi.name, g.department, g.level, g.public_access,\n"
                "       n.name AS neighbourhood, c.name AS city\n"
                "FROM poi_governmentoffice g\n"
                "  INNER JOIN poi_pointofinterest poi ON g.poi_id = poi.id\n"
                "  INNER JOIN poi_neighbourhood   n   ON poi.neighbourhood_id = n.id\n"
                "  INNER JOIN poi_city            c   ON n.city_id = c.id\n"
                + (f"WHERE g.level = '{govt_level}';" if govt_level else ";")
            )

    return render(request, 'poi/join_query.html', {
        'form':            form,
        'results':         results,
        'columns':         columns,
        'sql_explanation': sql_explanation,
        'result_count':    len(results),
    })


# ════════════════════════════════════════════
#  GENERIC POI CRUD
# ════════════════════════════════════════════

def poi_list(request):
    pois = PointOfInterest.objects.select_related(
        'neighbourhood', 'neighbourhood__city'
    ).order_by('poi_type', 'name')
    return render(request, 'poi/poi_list.html', {'pois': pois})


def poi_detail(request, pk):
    poi = get_object_or_404(
        PointOfInterest.objects.select_related('neighbourhood__city'), pk=pk
    )
    return render(request, 'poi/poi_detail.html', {'poi': poi})


def poi_create(request):
    form = POIForm(request.POST or None)
    if form.is_valid():
        poi = form.save()
        messages.success(request, f'"{poi.name}" created.')
        return redirect('poi:poi_detail', pk=poi.pk)
    return render(request, 'poi/poi_form.html', {'form': form, 'title': 'Add Point of Interest'})


def poi_edit(request, pk):
    poi  = get_object_or_404(PointOfInterest, pk=pk)
    form = POIForm(request.POST or None, instance=poi)
    if form.is_valid():
        form.save()
        messages.success(request, f'"{poi.name}" updated.')
        return redirect('poi:poi_detail', pk=poi.pk)
    return render(request, 'poi/poi_form.html', {'form': form, 'title': f'Edit {poi.name}'})


def poi_delete(request, pk):
    poi = get_object_or_404(PointOfInterest, pk=pk)
    if request.method == 'POST':
        name = poi.name
        poi.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('poi:poi_list')
    return render(request, 'poi/poi_confirm_delete.html', {'object': poi})


# ════════════════════════════════════════════
#  RESTAURANT CRUD
# ════════════════════════════════════════════

def restaurant_list(request):
    qs = Restaurant.objects.select_related(
        'poi', 'poi__neighbourhood__city', 'cuisine'
    ).order_by('poi__name')
    return render(request, 'poi/restaurant_list.html', {'restaurants': qs})


def restaurant_create(request):
    poi_form = POIForm(request.POST or None, initial={'poi_type': 'restaurant'})
    det_form = RestaurantForm(request.POST or None)
    if poi_form.is_valid() and det_form.is_valid():
        poi = poi_form.save(commit=False)
        poi.poi_type = 'restaurant'
        poi.save()
        r = det_form.save(commit=False)
        r.poi = poi
        r.save()
        messages.success(request, f'Restaurant "{poi.name}" created.')
        return redirect('poi:restaurant_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form,
        'title': 'Add Restaurant'
    })


def restaurant_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    poi_form   = POIForm(request.POST or None, instance=restaurant.poi)
    det_form   = RestaurantForm(request.POST or None, instance=restaurant)
    if poi_form.is_valid() and det_form.is_valid():
        poi_form.save()
        det_form.save()
        messages.success(request, 'Restaurant updated.')
        return redirect('poi:restaurant_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form,
        'title': f'Edit {restaurant.poi.name}'
    })


def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        name = restaurant.poi.name
        restaurant.poi.delete()   # cascades to Restaurant
        messages.success(request, f'"{name}" deleted.')
        return redirect('poi:restaurant_list')
    return render(request, 'poi/poi_confirm_delete.html', {'object': restaurant.poi})


# ════════════════════════════════════════════
#  MUSEUM CRUD  (same pattern as Restaurant)
# ════════════════════════════════════════════

def museum_list(request):
    qs = Museum.objects.select_related('poi', 'poi__neighbourhood__city', 'theme')
    return render(request, 'poi/museum_list.html', {'museums': qs})


def museum_create(request):
    poi_form = POIForm(request.POST or None, initial={'poi_type': 'museum'})
    det_form = MuseumForm(request.POST or None)
    if poi_form.is_valid() and det_form.is_valid():
        poi = poi_form.save(commit=False)
        poi.poi_type = 'museum'
        poi.save()
        m = det_form.save(commit=False)
        m.poi = poi
        m.save()
        messages.success(request, f'Museum "{poi.name}" created.')
        return redirect('poi:museum_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form, 'title': 'Add Museum'
    })


def museum_edit(request, pk):
    museum   = get_object_or_404(Museum, pk=pk)
    poi_form = POIForm(request.POST or None, instance=museum.poi)
    det_form = MuseumForm(request.POST or None, instance=museum)
    if poi_form.is_valid() and det_form.is_valid():
        poi_form.save()
        det_form.save()
        messages.success(request, 'Museum updated.')
        return redirect('poi:museum_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form, 'title': f'Edit {museum.poi.name}'
    })


def museum_delete(request, pk):
    museum = get_object_or_404(Museum, pk=pk)
    if request.method == 'POST':
        name = museum.poi.name
        museum.poi.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('poi:museum_list')
    return render(request, 'poi/poi_confirm_delete.html', {'object': museum.poi})


# ════════════════════════════════════════════
#  GOVERNMENT CRUD
# ════════════════════════════════════════════

def government_list(request):
    qs = GovernmentOffice.objects.select_related('poi', 'poi__neighbourhood__city')
    return render(request, 'poi/government_list.html', {'offices': qs})


def government_create(request):
    poi_form = POIForm(request.POST or None, initial={'poi_type': 'government'})
    det_form = GovernmentForm(request.POST or None)
    if poi_form.is_valid() and det_form.is_valid():
        poi = poi_form.save(commit=False)
        poi.poi_type = 'government'
        poi.save()
        g = det_form.save(commit=False)
        g.poi = poi
        g.save()
        messages.success(request, f'Office "{poi.name}" created.')
        return redirect('poi:government_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form, 'title': 'Add Government Office'
    })


def government_edit(request, pk):
    office   = get_object_or_404(GovernmentOffice, pk=pk)
    poi_form = POIForm(request.POST or None, instance=office.poi)
    det_form = GovernmentForm(request.POST or None, instance=office)
    if poi_form.is_valid() and det_form.is_valid():
        poi_form.save()
        det_form.save()
        messages.success(request, 'Office updated.')
        return redirect('poi:government_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form, 'title': f'Edit {office.poi.name}'
    })


def government_delete(request, pk):
    office = get_object_or_404(GovernmentOffice, pk=pk)
    if request.method == 'POST':
        name = office.poi.name
        office.poi.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('poi:government_list')
    return render(request, 'poi/poi_confirm_delete.html', {'object': office.poi})


# ════════════════════════════════════════════
#  BANK CRUD
# ════════════════════════════════════════════

def bank_list(request):
    qs = Bank.objects.select_related('poi', 'poi__neighbourhood__city')
    return render(request, 'poi/bank_list.html', {'banks': qs})


def bank_create(request):
    poi_form = POIForm(request.POST or None, initial={'poi_type': 'bank'})
    det_form = BankForm(request.POST or None)
    if poi_form.is_valid() and det_form.is_valid():
        poi = poi_form.save(commit=False)
        poi.poi_type = 'bank'
        poi.save()
        b = det_form.save(commit=False)
        b.poi = poi
        b.save()
        messages.success(request, f'Bank "{poi.name}" created.')
        return redirect('poi:bank_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form, 'title': 'Add Bank'
    })


def bank_edit(request, pk):
    bank     = get_object_or_404(Bank, pk=pk)
    poi_form = POIForm(request.POST or None, instance=bank.poi)
    det_form = BankForm(request.POST or None, instance=bank)
    if poi_form.is_valid() and det_form.is_valid():
        poi_form.save()
        det_form.save()
        messages.success(request, 'Bank updated.')
        return redirect('poi:bank_list')
    return render(request, 'poi/combined_form.html', {
        'poi_form': poi_form, 'detail_form': det_form, 'title': f'Edit {bank.poi.name}'
    })


def bank_delete(request, pk):
    bank = get_object_or_404(Bank, pk=pk)
    if request.method == 'POST':
        name = bank.poi.name
        bank.poi.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('poi:bank_list')
    return render(request, 'poi/poi_confirm_delete.html', {'object': bank.poi})
```

---

## 9. Templates

### Directory Structure

```
poi/
└── templates/
    └── poi/
        ├── base.html
        ├── dashboard.html
        ├── join_query.html      ← core teaching page
        ├── poi_list.html
        ├── poi_detail.html
        ├── poi_form.html
        ├── poi_confirm_delete.html
        ├── combined_form.html
        ├── restaurant_list.html
        ├── museum_list.html
        ├── government_list.html
        └── bank_list.html
```

### `base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}POI App{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: #f8f9fa; }
    .navbar { background: #1a3a5c !important; }
    .sql-box {
      background: #1e1e2e; color: #cdd6f4;
      font-family: monospace; font-size: .85rem;
      border-radius: 6px; padding: 1rem;
    }
    .badge-pk  { background: #198754; font-size: .7rem; }
    .badge-fk  { background: #0d6efd; font-size: .7rem; }
    .badge-o2o { background: #6f42c1; font-size: .7rem; }
  </style>
</head>
<body>
<nav class="navbar navbar-dark navbar-expand-lg mb-4">
  <div class="container">
    <a class="navbar-brand fw-bold" href="{% url 'poi:dashboard' %}">📍 POI Explorer</a>
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item"><a class="nav-link" href="{% url 'poi:join_query' %}">🔗 JOIN Queries</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'poi:poi_list' %}">All POIs</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'poi:restaurant_list' %}">🍴 Restaurants</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'poi:museum_list' %}">🏛 Museums</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'poi:government_list' %}">🏛 Government</a></li>
        <li class="nav-item"><a class="nav-link" href="{% url 'poi:bank_list' %}">🏦 Banks</a></li>
      </ul>
    </div>
  </div>
</nav>
<div class="container">
  {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
      {{ message }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
  {% endfor %}
  {% block content %}{% endblock %}
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

### `join_query.html` ← The Key Teaching Template

```html
{% extends "poi/base.html" %}
{% block title %}JOIN Query Explorer{% endblock %}
{% block content %}

<h2 class="mb-1">🔗 SQL JOIN Query Explorer</h2>
<p class="text-muted mb-4">
  Select a query type and optional filters. The results table and the SQL equivalent
  are shown below — demonstrating how Django ORM translates to SQL JOINs.
</p>

{# ── FILTER FORM ─────────────────────────────────── #}
<div class="card shadow-sm mb-4">
  <div class="card-header fw-bold">Query Controls</div>
  <div class="card-body">
    <form method="get" class="row g-3">
      <div class="col-md-6">
        <label class="form-label fw-semibold">JOIN Query Type</label>
        {{ form.query_type }}
      </div>
      <div class="col-md-3">
        <label class="form-label">City Filter</label>
        {{ form.filter_city }}
      </div>
      <div class="col-md-3">
        <label class="form-label">Neighbourhood Filter</label>
        {{ form.filter_neighbourhood }}
      </div>
      <div class="col-md-3">
        <label class="form-label">Cuisine Filter</label>
        {{ form.filter_cuisine }}
      </div>
      <div class="col-md-3">
        <label class="form-label">Museum Theme Filter</label>
        {{ form.filter_theme }}
      </div>
      <div class="col-md-3">
        <label class="form-label">Government Level</label>
        {{ form.filter_govt_level }}
      </div>
      <div class="col-md-3 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">▶ Run Query</button>
      </div>
    </form>
  </div>
</div>

{# ── SQL EXPLANATION ──────────────────────────────── #}
{% if sql_explanation %}
<div class="card shadow-sm mb-4">
  <div class="card-header fw-bold">📖 Equivalent SQL</div>
  <div class="card-body">
    <pre class="sql-box mb-0">{{ sql_explanation }}</pre>
    <div class="mt-2 small text-muted">
      <span class="badge badge-pk text-white me-1">PK</span> Primary Key &nbsp;
      <span class="badge badge-fk text-white me-1">FK</span> Foreign Key &nbsp;
      <span class="badge badge-o2o text-white">1:1</span> OneToOne
    </div>
  </div>
</div>
{% endif %}

{# ── RESULTS TABLE ────────────────────────────────── #}
{% if results %}
<div class="card shadow-sm">
  <div class="card-header d-flex justify-content-between align-items-center">
    <span class="fw-bold">Results</span>
    <span class="badge bg-secondary">{{ result_count }} row{{ result_count|pluralize }}</span>
  </div>
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-striped table-hover mb-0">
        <thead class="table-dark">
          <tr>{% for col in columns %}<th>{{ col }}</th>{% endfor %}</tr>
        </thead>
        <tbody>
          {% for row in results %}
          <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% elif form.is_bound %}
<div class="alert alert-info">No results found for that combination.</div>
{% endif %}

{% endblock %}
```

### `combined_form.html` (used by all POI create/edit views)

```html
{% extends "poi/base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<h2 class="mb-4">{{ title }}</h2>
<form method="post">
  {% csrf_token %}
  <div class="card shadow-sm mb-3">
    <div class="card-header fw-bold">📍 Base Point of Interest
      <span class="badge badge-pk text-white ms-2">PK: id</span>
    </div>
    <div class="card-body">
      <div class="row g-3">
        {% for field in poi_form %}
        <div class="col-md-6">
          <label class="form-label">{{ field.label }}</label>
          {{ field }}
          {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <div class="card shadow-sm mb-4">
    <div class="card-header fw-bold">🔗 Specific Details
      <span class="badge badge-o2o text-white ms-2">OneToOne → POI</span>
    </div>
    <div class="card-body">
      <div class="row g-3">
        {% for field in detail_form %}
        <div class="col-md-6">
          <label class="form-label">{{ field.label }}</label>
          {{ field }}
          {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
        </div>
        {% endfor %}
      </div>
    </div>
  </div>

  <div class="d-flex gap-2">
    <button type="submit" class="btn btn-success">💾 Save</button>
    <a href="javascript:history.back()" class="btn btn-outline-secondary">Cancel</a>
  </div>
</form>
{% endblock %}
```

### `poi_confirm_delete.html`

```html
{% extends "poi/base.html" %}
{% block content %}
<div class="card shadow-sm" style="max-width:500px;margin:auto">
  <div class="card-header bg-danger text-white fw-bold">Confirm Delete</div>
  <div class="card-body">
    <p>Are you sure you want to delete <strong>{{ object }}</strong>?</p>
    <p class="text-muted small">This will also delete all related subtype records (cascade).</p>
    <form method="post">
      {% csrf_token %}
      <button type="submit" class="btn btn-danger me-2">Yes, Delete</button>
      <a href="javascript:history.back()" class="btn btn-secondary">Cancel</a>
    </form>
  </div>
</div>
{% endblock %}
```

---

### `dashboard.html`

```html
{% extends "poi/base.html" %}
{% block title %}Dashboard — POI Explorer{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-4">
  <div>
    <h2 class="mb-0">📍 Points of Interest Explorer</h2>
    <p class="text-muted mb-0">A Django demo of Primary Keys, Foreign Keys &amp; SQL JOINs</p>
  </div>
  <a href="{% url 'poi:join_query' %}" class="btn btn-primary btn-lg">🔗 Open JOIN Explorer</a>
</div>

{# ── STAT CARDS ── #}
<div class="row g-3 mb-4">
  <div class="col-sm-6 col-md-3">
    <div class="card shadow-sm text-center h-100">
      <div class="card-body">
        <div class="display-5 fw-bold text-primary">{{ total_poi }}</div>
        <div class="text-muted small mt-1">Total POIs</div>
        <a href="{% url 'poi:poi_list' %}" class="btn btn-sm btn-outline-primary mt-2">View All</a>
      </div>
    </div>
  </div>
  <div class="col-sm-6 col-md-3">
    <div class="card shadow-sm text-center h-100">
      <div class="card-body">
        <div class="display-5 fw-bold text-warning">{{ total_restaurants }}</div>
        <div class="text-muted small mt-1">Restaurants</div>
        <a href="{% url 'poi:restaurant_list' %}" class="btn btn-sm btn-outline-warning mt-2">View</a>
      </div>
    </div>
  </div>
  <div class="col-sm-6 col-md-3">
    <div class="card shadow-sm text-center h-100">
      <div class="card-body">
        <div class="display-5 fw-bold text-info">{{ total_museums }}</div>
        <div class="text-muted small mt-1">Museums</div>
        <a href="{% url 'poi:museum_list' %}" class="btn btn-sm btn-outline-info mt-2">View</a>
      </div>
    </div>
  </div>
  <div class="col-sm-6 col-md-3">
    <div class="card shadow-sm text-center h-100">
      <div class="card-body">
        <div class="display-5 fw-bold text-success">{{ total_banks }}</div>
        <div class="text-muted small mt-1">Banks</div>
        <a href="{% url 'poi:bank_list' %}" class="btn btn-sm btn-outline-success mt-2">View</a>
      </div>
    </div>
  </div>
</div>

{# ── QUICK-ADD BUTTONS ── #}
<div class="card shadow-sm mb-4">
  <div class="card-header fw-bold">➕ Add New Point of Interest</div>
  <div class="card-body d-flex flex-wrap gap-2">
    <a href="{% url 'poi:restaurant_create' %}" class="btn btn-outline-warning">🍴 Restaurant</a>
    <a href="{% url 'poi:museum_create' %}"     class="btn btn-outline-info">🏛 Museum</a>
    <a href="{% url 'poi:government_create' %}" class="btn btn-outline-secondary">🏢 Government Office</a>
    <a href="{% url 'poi:bank_create' %}"       class="btn btn-outline-success">🏦 Bank</a>
  </div>
</div>

{# ── KEY CONCEPTS ── #}
<div class="card shadow-sm mb-4">
  <div class="card-header fw-bold">📚 Key Database Concepts in This App</div>
  <div class="card-body">
    <div class="row g-3">
      <div class="col-md-4">
        <div class="border rounded p-3 h-100">
          <h6 class="fw-bold"><span class="badge bg-success me-1">PK</span> Primary Key</h6>
          <p class="small text-muted mb-0">
            Every model has an auto-generated <code>id</code> field — the unique identifier
            for each row. Django sets this automatically.
          </p>
        </div>
      </div>
      <div class="col-md-4">
        <div class="border rounded p-3 h-100">
          <h6 class="fw-bold"><span class="badge bg-primary me-1">FK</span> Foreign Key</h6>
          <p class="small text-muted mb-0">
            <code>ForeignKey(Model)</code> stores the PK of another table's row.
            Example: <code>Neighbourhood.city_id</code> stores a City's PK.
          </p>
        </div>
      </div>
      <div class="col-md-4">
        <div class="border rounded p-3 h-100">
          <h6 class="fw-bold"><span class="badge bg-purple me-1" style="background:#6f42c1">1:1</span> OneToOne</h6>
          <p class="small text-muted mb-0">
            <code>OneToOneField</code> is a FK + UNIQUE constraint. Each Restaurant
            links to exactly one PointOfInterest and vice-versa.
          </p>
        </div>
      </div>
    </div>
  </div>
</div>

{# ── CITIES / NEIGHBOURHOODS ── #}
<div class="card shadow-sm">
  <div class="card-header fw-bold">🗺 Cities &amp; Neighbourhoods</div>
  <div class="card-body p-0">
    <table class="table table-hover mb-0">
      <thead class="table-dark">
        <tr>
          <th>City <span class="badge bg-success ms-1">PK</span></th>
          <th>Country</th>
          <th>Neighbourhoods</th>
          <th>POIs</th>
        </tr>
      </thead>
      <tbody>
        {% for city in cities %}
        <tr>
          <td><strong>{{ city.name }}</strong> <span class="text-muted small">#{{ city.pk }}</span></td>
          <td>{{ city.country }}</td>
          <td>
            {% for n in city.neighbourhoods.all %}
              <span class="badge bg-light text-dark border me-1">{{ n.name }}</span>
            {% empty %}
              <span class="text-muted small">—</span>
            {% endfor %}
          </td>
          <td>{{ city.neighbourhoods.all|length }}</td>
        </tr>
        {% empty %}
        <tr><td colspan="4" class="text-center text-muted">No cities yet. Run <code>python manage.py seed_data</code></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

{% endblock %}
```

---

### `poi_list.html`

```html
{% extends "poi/base.html" %}
{% block title %}All Points of Interest{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-3">
  <h2 class="mb-0">All Points of Interest</h2>
  <a href="{% url 'poi:poi_create' %}" class="btn btn-success">➕ Add POI</a>
</div>

<div class="card shadow-sm">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-striped table-hover mb-0">
        <thead class="table-dark">
          <tr>
            <th>ID <span class="badge bg-success ms-1">PK</span></th>
            <th>Name</th>
            <th>Type</th>
            <th>Neighbourhood <span class="badge bg-primary ms-1">FK</span></th>
            <th>City</th>
            <th>Latitude</th>
            <th>Longitude</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for poi in pois %}
          <tr>
            <td><code>{{ poi.pk }}</code></td>
            <td><a href="{% url 'poi:poi_detail' poi.pk %}">{{ poi.name }}</a></td>
            <td>
              {% if poi.poi_type == 'restaurant' %}<span class="badge bg-warning text-dark">🍴 Restaurant</span>
              {% elif poi.poi_type == 'museum' %}<span class="badge bg-info text-dark">🏛 Museum</span>
              {% elif poi.poi_type == 'government' %}<span class="badge bg-secondary">🏢 Government</span>
              {% elif poi.poi_type == 'bank' %}<span class="badge bg-success">🏦 Bank</span>
              {% endif %}
            </td>
            <td>
              {% if poi.neighbourhood %}
                {{ poi.neighbourhood.name }}
                <span class="text-muted small">(FK→{{ poi.neighbourhood.pk }})</span>
              {% else %}—{% endif %}
            </td>
            <td>{{ poi.neighbourhood.city.name|default:"—" }}</td>
            <td><code>{{ poi.latitude }}</code></td>
            <td><code>{{ poi.longitude }}</code></td>
            <td>
              <a href="{% url 'poi:poi_edit' poi.pk %}" class="btn btn-sm btn-outline-primary me-1">Edit</a>
              <a href="{% url 'poi:poi_delete' poi.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="8" class="text-center text-muted py-4">No POIs found.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

{% endblock %}
```

---

### `poi_detail.html`

```html
{% extends "poi/base.html" %}
{% block title %}{{ poi.name }}{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-start mb-4">
  <div>
    <h2 class="mb-0">{{ poi.name }}</h2>
    <span class="text-muted small">Primary Key (id): <code>{{ poi.pk }}</code></span>
  </div>
  <div class="d-flex gap-2">
    <a href="{% url 'poi:poi_edit' poi.pk %}" class="btn btn-outline-primary">✏️ Edit</a>
    <a href="{% url 'poi:poi_delete' poi.pk %}" class="btn btn-outline-danger">🗑 Delete</a>
    <a href="{% url 'poi:poi_list' %}" class="btn btn-outline-secondary">← Back</a>
  </div>
</div>

<div class="row g-3">
  {# ── Base POI Info ── #}
  <div class="col-md-6">
    <div class="card shadow-sm h-100">
      <div class="card-header fw-bold">
        📍 Base POI Data
        <span class="badge bg-success ms-2">PK: {{ poi.pk }}</span>
      </div>
      <div class="card-body">
        <table class="table table-sm mb-0">
          <tr><th>Name</th><td>{{ poi.name }}</td></tr>
          <tr><th>Type</th><td>{{ poi.get_poi_type_display }}</td></tr>
          <tr><th>Latitude</th><td><code>{{ poi.latitude }}</code></td></tr>
          <tr><th>Longitude</th><td><code>{{ poi.longitude }}</code></td></tr>
          <tr><th>Address</th><td>{{ poi.address|default:"—" }}</td></tr>
          <tr><th>Phone</th><td>{{ poi.phone|default:"—" }}</td></tr>
          <tr><th>Website</th><td>
            {% if poi.website %}<a href="{{ poi.website }}" target="_blank">{{ poi.website }}</a>
            {% else %}—{% endif %}
          </td></tr>
          <tr>
            <th>Neighbourhood <span class="badge bg-primary" style="font-size:.65rem">FK</span></th>
            <td>
              {% if poi.neighbourhood %}
                {{ poi.neighbourhood.name }}
                <span class="text-muted small">(neighbourhood.id = {{ poi.neighbourhood.pk }})</span>
              {% else %}—{% endif %}
            </td>
          </tr>
          <tr>
            <th>City <span class="badge bg-primary" style="font-size:.65rem">FK via neighbourhood</span></th>
            <td>{{ poi.neighbourhood.city.name|default:"—" }}</td>
          </tr>
        </table>
      </div>
    </div>
  </div>

  {# ── Subtype Details ── #}
  <div class="col-md-6">
    <div class="card shadow-sm h-100">
      <div class="card-header fw-bold">
        🔗 Subtype Details
        <span class="badge bg-purple text-white ms-2" style="background:#6f42c1!important">OneToOne → POI #{{ poi.pk }}</span>
      </div>
      <div class="card-body">
        {% if poi.poi_type == 'restaurant' and poi.restaurant %}
          {% with r=poi.restaurant %}
          <table class="table table-sm mb-0">
            <tr><th>Cuisine <span class="badge bg-primary" style="font-size:.65rem">FK</span></th>
                <td>{{ r.cuisine }} <span class="text-muted small">(cuisine.id={{ r.cuisine.pk }})</span></td></tr>
            <tr><th>Price Range</th><td>{{ r.price_range }}</td></tr>
            <tr><th>Seating</th><td>{{ r.seating_capacity }}</td></tr>
            <tr><th>Michelin ★</th><td>{% if r.michelin_stars %}{{ r.michelin_stars }}{% else %}—{% endif %}</td></tr>
            <tr><th>Delivery</th><td>{% if r.has_delivery %}✓{% else %}✗{% endif %}</td></tr>
            <tr><th>Takeout</th><td>{% if r.has_takeout %}✓{% else %}✗{% endif %}</td></tr>
            <tr><th>Hours</th><td>{{ r.opening_hours|default:"—" }}</td></tr>
          </table>
          {% endwith %}
        {% elif poi.poi_type == 'museum' and poi.museum %}
          {% with m=poi.museum %}
          <table class="table table-sm mb-0">
            <tr><th>Theme <span class="badge bg-primary" style="font-size:.65rem">FK</span></th>
                <td>{{ m.theme }} <span class="text-muted small">(theme.id={{ m.theme.pk }})</span></td></tr>
            <tr><th>Exhibition</th><td>{{ m.current_exhibition|default:"—" }}</td></tr>
            <tr><th>Admission</th><td>{% if m.is_free %}Free{% else %}${{ m.admission_fee }}{% endif %}</td></tr>
            <tr><th>Founded</th><td>{{ m.founding_year|default:"—" }}</td></tr>
            <tr><th>Floors</th><td>{{ m.num_floors }}</td></tr>
          </table>
          {% endwith %}
        {% elif poi.poi_type == 'government' and poi.government %}
          {% with g=poi.government %}
          <table class="table table-sm mb-0">
            <tr><th>Department</th><td>{{ g.department }}</td></tr>
            <tr><th>Level</th><td>{{ g.get_level_display }}</td></tr>
            <tr><th>Official Name</th><td>{{ g.official_name|default:"—" }}</td></tr>
            <tr><th>Services</th><td>{{ g.services_offered|default:"—" }}</td></tr>
            <tr><th>Appointment</th><td>{% if g.appointment_required %}Required{% else %}Walk-in OK{% endif %}</td></tr>
            <tr><th>Public Access</th><td>{% if g.public_access %}✓ Yes{% else %}✗ No{% endif %}</td></tr>
          </table>
          {% endwith %}
        {% elif poi.poi_type == 'bank' and poi.bank %}
          {% with b=poi.bank %}
          <table class="table table-sm mb-0">
            <tr><th>Bank Name</th><td>{{ b.bank_name }}</td></tr>
            <tr><th>Type</th><td>{{ b.get_bank_type_display }}</td></tr>
            <tr><th>SWIFT</th><td>{{ b.swift_code|default:"—" }}</td></tr>
            <tr><th>ATM</th><td>{% if b.has_atm %}✓ Yes ({{ b.num_atms }}){% else %}✗ No{% endif %}</td></tr>
            <tr><th>Drive-Through</th><td>{% if b.drive_through %}✓{% else %}✗{% endif %}</td></tr>
            <tr><th>Foreign Currency</th><td>{% if b.accepts_foreign_currency %}✓{% else %}✗{% endif %}</td></tr>
          </table>
          {% endwith %}
        {% else %}
          <p class="text-muted">No subtype details recorded yet.</p>
        {% endif %}
      </div>
    </div>
  </div>
</div>

{# ── Nearby POIs ── #}
{% if poi.nearby_from.exists %}
<div class="card shadow-sm mt-3">
  <div class="card-header fw-bold">🗺 Nearby POIs <span class="badge bg-secondary ms-1">Many-to-Many via NearbyPOI junction table</span></div>
  <div class="card-body p-0">
    <table class="table table-sm mb-0">
      <thead class="table-light"><tr><th>Nearby POI</th><th>Type</th><th>Walk (min)</th></tr></thead>
      <tbody>
        {% for link in poi.nearby_from.select_related %}
        <tr>
          <td><a href="{% url 'poi:poi_detail' link.to_poi.pk %}">{{ link.to_poi.name }}</a></td>
          <td>{{ link.to_poi.get_poi_type_display }}</td>
          <td>{{ link.walk_minutes }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endif %}

{% endblock %}
```

---

### `poi_form.html`

```html
{% extends "poi/base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-4">
  <h2>{{ title }}</h2>
  <a href="{% url 'poi:poi_list' %}" class="btn btn-outline-secondary">← Back to List</a>
</div>

<div class="card shadow-sm" style="max-width:700px">
  <div class="card-header fw-bold">
    📍 Point of Interest
    <span class="badge bg-success ms-2">PK: auto-assigned on save</span>
  </div>
  <div class="card-body">
    <form method="post">
      {% csrf_token %}
      <div class="row g-3">
        {% for field in form %}
        <div class="col-md-6">
          <label class="form-label fw-semibold">{{ field.label }}</label>
          {{ field }}
          {% if field.errors %}
            <div class="text-danger small mt-1">{{ field.errors }}</div>
          {% endif %}
          {% if field.help_text %}
            <div class="text-muted small">{{ field.help_text }}</div>
          {% endif %}
        </div>
        {% endfor %}
      </div>
      <div class="d-flex gap-2 mt-4">
        <button type="submit" class="btn btn-success">💾 Save</button>
        <a href="{% url 'poi:poi_list' %}" class="btn btn-outline-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>

{% endblock %}
```

---

### `restaurant_list.html`

```html
{% extends "poi/base.html" %}
{% block title %}Restaurants{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-3">
  <h2 class="mb-0">🍴 Restaurants</h2>
  <a href="{% url 'poi:restaurant_create' %}" class="btn btn-success">➕ Add Restaurant</a>
</div>

<div class="card shadow-sm mb-3">
  <div class="card-body py-2 px-3 small text-muted">
    <strong>Tables involved:</strong>
    <code>poi_restaurant</code>
    <span class="badge bg-purple text-white mx-1" style="background:#6f42c1!important">OneToOne</span>→
    <code>poi_pointofinterest</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_cuisine</code> &amp;
    <code>poi_neighbourhood</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_city</code>
  </div>
</div>

<div class="card shadow-sm">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-striped table-hover mb-0">
        <thead class="table-dark">
          <tr>
            <th>ID <span class="badge bg-success ms-1">PK</span></th>
            <th>Name</th>
            <th>Cuisine <span class="badge bg-primary ms-1">FK</span></th>
            <th>Price</th>
            <th>Michelin ★</th>
            <th>Delivery</th>
            <th>Takeout</th>
            <th>Neighbourhood</th>
            <th>City</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for r in restaurants %}
          <tr>
            <td><code>{{ r.pk }}</code></td>
            <td><a href="{% url 'poi:poi_detail' r.poi.pk %}">{{ r.poi.name }}</a></td>
            <td>{{ r.cuisine }}</td>
            <td>{{ r.price_range }}</td>
            <td>{% if r.michelin_stars %}{{ r.michelin_stars }}★{% else %}—{% endif %}</td>
            <td>{% if r.has_delivery %}✓{% else %}✗{% endif %}</td>
            <td>{% if r.has_takeout %}✓{% else %}✗{% endif %}</td>
            <td>{{ r.poi.neighbourhood.name|default:"—" }}</td>
            <td>{{ r.poi.neighbourhood.city.name|default:"—" }}</td>
            <td>
              <a href="{% url 'poi:restaurant_edit' r.pk %}" class="btn btn-sm btn-outline-primary me-1">Edit</a>
              <a href="{% url 'poi:restaurant_delete' r.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="10" class="text-center text-muted py-4">No restaurants yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

{% endblock %}
```

---

### `museum_list.html`

```html
{% extends "poi/base.html" %}
{% block title %}Museums{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-3">
  <h2 class="mb-0">🏛 Museums</h2>
  <a href="{% url 'poi:museum_create' %}" class="btn btn-success">➕ Add Museum</a>
</div>

<div class="card shadow-sm mb-3">
  <div class="card-body py-2 px-3 small text-muted">
    <strong>Tables involved:</strong>
    <code>poi_museum</code>
    <span class="badge bg-purple text-white mx-1" style="background:#6f42c1!important">OneToOne</span>→
    <code>poi_pointofinterest</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_museumtheme</code> &amp;
    <code>poi_neighbourhood</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_city</code>
  </div>
</div>

<div class="card shadow-sm">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-striped table-hover mb-0">
        <thead class="table-dark">
          <tr>
            <th>ID <span class="badge bg-success ms-1">PK</span></th>
            <th>Name</th>
            <th>Theme <span class="badge bg-primary ms-1">FK</span></th>
            <th>Exhibition</th>
            <th>Admission</th>
            <th>Founded</th>
            <th>Neighbourhood</th>
            <th>City</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for m in museums %}
          <tr>
            <td><code>{{ m.pk }}</code></td>
            <td><a href="{% url 'poi:poi_detail' m.poi.pk %}">{{ m.poi.name }}</a></td>
            <td>{{ m.theme }}</td>
            <td>{{ m.current_exhibition|default:"—"|truncatechars:40 }}</td>
            <td>{% if m.is_free %}<span class="badge bg-success">Free</span>{% else %}\${{ m.admission_fee }}{% endif %}</td>
            <td>{{ m.founding_year|default:"—" }}</td>
            <td>{{ m.poi.neighbourhood.name|default:"—" }}</td>
            <td>{{ m.poi.neighbourhood.city.name|default:"—" }}</td>
            <td>
              <a href="{% url 'poi:museum_edit' m.pk %}" class="btn btn-sm btn-outline-primary me-1">Edit</a>
              <a href="{% url 'poi:museum_delete' m.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="9" class="text-center text-muted py-4">No museums yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

{% endblock %}
```

---

### `government_list.html`

```html
{% extends "poi/base.html" %}
{% block title %}Government Offices{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-3">
  <h2 class="mb-0">🏢 Government Offices</h2>
  <a href="{% url 'poi:government_create' %}" class="btn btn-success">➕ Add Office</a>
</div>

<div class="card shadow-sm mb-3">
  <div class="card-body py-2 px-3 small text-muted">
    <strong>Tables involved:</strong>
    <code>poi_governmentoffice</code>
    <span class="badge bg-purple text-white mx-1" style="background:#6f42c1!important">OneToOne</span>→
    <code>poi_pointofinterest</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_neighbourhood</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_city</code>
  </div>
</div>

<div class="card shadow-sm">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-striped table-hover mb-0">
        <thead class="table-dark">
          <tr>
            <th>ID <span class="badge bg-success ms-1">PK</span></th>
            <th>Office Name</th>
            <th>Department</th>
            <th>Level</th>
            <th>Public Access</th>
            <th>Appointment</th>
            <th>Neighbourhood</th>
            <th>City</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for g in offices %}
          <tr>
            <td><code>{{ g.pk }}</code></td>
            <td><a href="{% url 'poi:poi_detail' g.poi.pk %}">{{ g.poi.name }}</a></td>
            <td>{{ g.department }}</td>
            <td>
              {% if g.level == 'federal' %}<span class="badge bg-danger">Federal</span>
              {% elif g.level == 'state' %}<span class="badge bg-warning text-dark">State/Provincial</span>
              {% else %}<span class="badge bg-secondary">Municipal</span>
              {% endif %}
            </td>
            <td>{% if g.public_access %}✓ Yes{% else %}✗ No{% endif %}</td>
            <td>{% if g.appointment_required %}Required{% else %}Walk-in{% endif %}</td>
            <td>{{ g.poi.neighbourhood.name|default:"—" }}</td>
            <td>{{ g.poi.neighbourhood.city.name|default:"—" }}</td>
            <td>
              <a href="{% url 'poi:government_edit' g.pk %}" class="btn btn-sm btn-outline-primary me-1">Edit</a>
              <a href="{% url 'poi:government_delete' g.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="9" class="text-center text-muted py-4">No government offices yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

{% endblock %}
```

---

### `bank_list.html`

```html
{% extends "poi/base.html" %}
{% block title %}Banks{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-3">
  <h2 class="mb-0">🏦 Banks</h2>
  <a href="{% url 'poi:bank_create' %}" class="btn btn-success">➕ Add Bank</a>
</div>

<div class="card shadow-sm mb-3">
  <div class="card-body py-2 px-3 small text-muted">
    <strong>Tables involved:</strong>
    <code>poi_bank</code>
    <span class="badge bg-purple text-white mx-1" style="background:#6f42c1!important">OneToOne</span>→
    <code>poi_pointofinterest</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_neighbourhood</code>
    <span class="badge bg-primary mx-1">FK</span>→
    <code>poi_city</code>
  </div>
</div>

<div class="card shadow-sm">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-striped table-hover mb-0">
        <thead class="table-dark">
          <tr>
            <th>ID <span class="badge bg-success ms-1">PK</span></th>
            <th>Branch Name</th>
            <th>Bank Name</th>
            <th>Type</th>
            <th>ATM</th>
            <th># ATMs</th>
            <th>Drive-Through</th>
            <th>Foreign Currency</th>
            <th>Neighbourhood</th>
            <th>City</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for b in banks %}
          <tr>
            <td><code>{{ b.pk }}</code></td>
            <td><a href="{% url 'poi:poi_detail' b.poi.pk %}">{{ b.poi.name }}</a></td>
            <td>{{ b.bank_name }}</td>
            <td>{{ b.get_bank_type_display }}</td>
            <td>{% if b.has_atm %}<span class="badge bg-success">✓ Yes</span>{% else %}<span class="badge bg-secondary">✗ No</span>{% endif %}</td>
            <td>{{ b.num_atms }}</td>
            <td>{% if b.drive_through %}✓{% else %}—{% endif %}</td>
            <td>{% if b.accepts_foreign_currency %}✓{% else %}—{% endif %}</td>
            <td>{{ b.poi.neighbourhood.name|default:"—" }}</td>
            <td>{{ b.poi.neighbourhood.city.name|default:"—" }}</td>
            <td>
              <a href="{% url 'poi:bank_edit' b.pk %}" class="btn btn-sm btn-outline-primary me-1">Edit</a>
              <a href="{% url 'poi:bank_delete' b.pk %}" class="btn btn-sm btn-outline-danger">Delete</a>
            </td>
          </tr>
          {% empty %}
          <tr><td colspan="11" class="text-center text-muted py-4">No banks yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>

{% endblock %}
```

---

## 10. Sample Data (Management Command)

Create `poi/management/commands/seed_data.py`:

```python
from django.core.management.base import BaseCommand
from poi.models import (
    City, Neighbourhood, Cuisine, MuseumTheme,
    PointOfInterest, Restaurant, Museum, GovernmentOffice, Bank, NearbyPOI
)

class Command(BaseCommand):
    help = 'Seed the database with sample Points of Interest'

    def handle(self, *args, **kwargs):
        # Cities
        toronto = City.objects.create(name='Toronto', country='Canada')
        montreal = City.objects.create(name='Montreal', country='Canada')

        # Neighbourhoods (FK → City)
        downtown   = Neighbourhood.objects.create(name='Downtown',        city=toronto)
        kensington = Neighbourhood.objects.create(name='Kensington Market', city=toronto)
        vieux      = Neighbourhood.objects.create(name='Vieux-Montréal',  city=montreal)

        # Lookup tables
        italian  = Cuisine.objects.create(name='Italian',   description='Pasta, pizza, and more')
        japanese = Cuisine.objects.create(name='Japanese',  description='Sushi, ramen, tempura')
        canadian = Cuisine.objects.create(name='Canadian',  description='Poutine, maple syrup')

        history_theme = MuseumTheme.objects.create(name='History',  description='Historical artifacts')
        science_theme = MuseumTheme.objects.create(name='Science',  description='STEM exhibits')
        art_theme     = MuseumTheme.objects.create(name='Fine Art', description='Paintings and sculpture')

        # POIs + sub-types
        # ── Restaurants
        for data in [
            dict(name="Terroni",      lat=43.6457, lon=-79.3947, nbhd=downtown,   cuisine=italian,  price='$$',  stars=0, delivery=False),
            dict(name="Yuzu No Hana", lat=43.6548, lon=-79.4003, nbhd=kensington, cuisine=japanese, price='$$$', stars=1, delivery=True),
            dict(name="Le Mousso",    lat=45.5206, lon=-73.5482, nbhd=vieux,      cuisine=canadian, price='$$$$',stars=1, delivery=False),
        ]:
            poi = PointOfInterest.objects.create(
                name=data['name'], latitude=data['lat'], longitude=data['lon'],
                poi_type='restaurant', neighbourhood=data['nbhd']
            )
            Restaurant.objects.create(
                poi=poi, cuisine=data['cuisine'], price_range=data['price'],
                michelin_stars=data['stars'], has_delivery=data['delivery'], seating_capacity=60
            )

        # ── Museums
        for data in [
            dict(name="ROM",           lat=43.6677, lon=-79.3948, nbhd=downtown,   theme=history_theme, fee=23, free=False, year=1914),
            dict(name="Ontario Science Centre", lat=43.7175, lon=-79.3390, nbhd=downtown, theme=science_theme, fee=28, free=False, year=1969),
            dict(name="McCord Museum", lat=45.5035, lon=-73.5731, nbhd=vieux,      theme=history_theme, fee=0,  free=True,  year=1921),
        ]:
            poi = PointOfInterest.objects.create(
                name=data['name'], latitude=data['lat'], longitude=data['lon'],
                poi_type='museum', neighbourhood=data['nbhd']
            )
            Museum.objects.create(
                poi=poi, theme=data['theme'], admission_fee=data['fee'],
                is_free=data['free'], founding_year=data['year'],
                current_exhibition="Current Highlights"
            )

        # ── Government
        poi = PointOfInterest.objects.create(
            name="Toronto City Hall", latitude=43.6525, longitude=-79.3838,
            poi_type='government', neighbourhood=downtown
        )
        GovernmentOffice.objects.create(
            poi=poi, department="City Clerk", level="municipal",
            services_offered="Permits, Licences, Marriage Certificates", public_access=True
        )

        # ── Banks
        for data in [
            dict(name="TD Bank",  bname="TD Bank",  type='commercial', nbhd=downtown,   atm=True, dt=True),
            dict(name="Desjardins", bname="Desjardins", type='credit_union', nbhd=vieux, atm=True, dt=False),
        ]:
            poi = PointOfInterest.objects.create(
                name=data['name'], latitude=43.65, longitude=-79.38,
                poi_type='bank', neighbourhood=data['nbhd']
            )
            Bank.objects.create(
                poi=poi, bank_name=data['bname'], bank_type=data['type'],
                has_atm=data['atm'], num_atms=3, drive_through=data['dt']
            )

        # ── Nearby links (Many-to-Many cross-join demo)
        pois = list(PointOfInterest.objects.filter(neighbourhood=downtown))
        for i in range(len(pois)-1):
            NearbyPOI.objects.get_or_create(
                from_poi=pois[i], to_poi=pois[i+1], defaults={'walk_minutes': 5+i*2}
            )

        self.stdout.write(self.style.SUCCESS('✅ Sample data seeded successfully!'))
```

Run it:

```bash
python manage.py seed_data
```

---

## 11. Running the Application

```bash
python manage.py createsuperuser   # for /admin access
python manage.py runserver
```

| URL | Purpose |
|---|---|
| `http://localhost:8000/` | Dashboard |
| `http://localhost:8000/join-query/` | SQL JOIN Explorer |
| `http://localhost:8000/poi/` | All POIs list |
| `http://localhost:8000/restaurants/` | Restaurant CRUD |
| `http://localhost:8000/museums/` | Museum CRUD |
| `http://localhost:8000/government/` | Government CRUD |
| `http://localhost:8000/banks/` | Bank CRUD |
| `http://localhost:8000/admin/` | Django Admin |

---

## 12. Key Concepts for Students

### Primary Key vs Foreign Key

| Concept | Django | SQL |
|---|---|---|
| **Primary Key** | `id` (auto on every model) | `INT PRIMARY KEY AUTO_INCREMENT` |
| **Foreign Key** | `ForeignKey(Model, on_delete=...)` | `FOREIGN KEY (col) REFERENCES table(id)` |
| **One-to-One** | `OneToOneField(Model, ...)` | FK + UNIQUE constraint |
| **Many-to-Many** | `ManyToManyField` or manual junction | Junction table with two FKs |

### ORM → SQL Translation

```python
# Django ORM
Restaurant.objects.select_related('poi', 'cuisine').filter(cuisine__name='Italian')

# Equivalent SQL
SELECT r.*, p.*, c.*
FROM poi_restaurant r
  INNER JOIN poi_pointofinterest p ON r.poi_id = p.id
  INNER JOIN poi_cuisine         c ON r.cuisine_id = c.id
WHERE c.name = 'Italian';
```

### `select_related` vs `prefetch_related`

- **`select_related`** — uses SQL JOIN; best for ForeignKey / OneToOne (single query)
- **`prefetch_related`** — uses separate queries + Python join; best for ManyToMany

### `on_delete` Options

| Option | Behaviour |
|---|---|
| `CASCADE` | Delete child when parent is deleted |
| `SET_NULL` | Set FK to NULL (field must be `null=True`) |
| `PROTECT` | Prevent parent deletion if children exist |
| `DO_NOTHING` | Database decides (risky) |

---

## 13. Project File Structure (Final)

```
poi_project/
├── manage.py
├── poi_project/
│   ├── settings.py
│   └── urls.py
└── poi/
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    ├── admin.py
    ├── management/
    │   └── commands/
    │       └── seed_data.py
    └── templates/
        └── poi/
            ├── base.html
            ├── dashboard.html
            ├── join_query.html
            ├── combined_form.html
            ├── poi_list.html
            ├── poi_detail.html
            ├── poi_form.html
            ├── poi_confirm_delete.html
            ├── restaurant_list.html
            ├── museum_list.html
            ├── government_list.html
            └── bank_list.html
```
