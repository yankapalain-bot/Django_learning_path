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