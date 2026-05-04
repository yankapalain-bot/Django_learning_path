from django.db import models

# Create your models here.
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