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