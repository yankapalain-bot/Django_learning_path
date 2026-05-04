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