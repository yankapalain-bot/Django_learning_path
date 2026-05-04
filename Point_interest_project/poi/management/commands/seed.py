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