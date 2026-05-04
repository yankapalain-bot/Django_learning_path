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