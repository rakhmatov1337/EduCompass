import json
from django.db.models import Q
from django_filters import rest_framework as filters
from main.models import Course, Event, Day


def parse_int_list(raw):
    """
    Turn "[1,2]", "1,2", [1,2], or ("1","2") into a List[int].
    """
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        out = []
        for v in raw:
            try:
                out.append(int(v))
            except (TypeError, ValueError):
                continue
        return out

    s = raw.strip()
    # JSON array style
    if s.startswith('[') and s.endswith(']'):
        try:
            arr = json.loads(s)
            return [int(x) for x in arr]
        except Exception:
            s = s[1:-1]

    # comma-separated fallback
    return [int(x) for x in s.split(',') if x.strip().isdigit()]


def parse_str_list(raw):
    """
    Turn "[a,b]", "a,b", ["a","b"] into a List[str].
    """
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x).strip() for x in raw if x]

    s = raw.strip()
    if s.startswith('[') and s.endswith(']'):
        try:
            arr = json.loads(s)
            return [str(x).strip() for x in arr]
        except Exception:
            s = s[1:-1]

    return [x.strip() for x in s.split(',') if x.strip()]


class CourseFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price",        lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price",        lookup_expr="lte")
    total_places_min = filters.NumberFilter(
        field_name="total_places", lookup_expr="gte")
    total_places_max = filters.NumberFilter(
        field_name="total_places", lookup_expr="lte")

    # multi-value filters via custom methods
    category_ids = filters.CharFilter(method="filter_category")
    edu_center_ids = filters.CharFilter(method="filter_center")
    teacher_gender = filters.CharFilter(method="filter_gender")
    day = filters.CharFilter(method="filter_day")

    class Meta:
        model = Course
        fields = []

    def filter_category(self, qs, name, raw):
        ids = parse_int_list(raw)
        if not ids:
            return qs
        filtered = qs.filter(category__id__in=ids)
        return filtered if filtered.exists() else qs

    def filter_center(self, qs, name, raw):
        ids = parse_int_list(raw)
        if not ids:
            return qs
        filtered = qs.filter(branch__edu_center__id__in=ids)
        return filtered if filtered.exists() else qs

    def filter_gender(self, qs, name, raw):
        vals = [g.lower() for g in parse_str_list(raw)]
        if not vals:
            return qs
        q = Q()
        for v in vals:
            q |= Q(teacher__gender__iexact=v)
        filtered = qs.filter(q)
        return filtered if filtered.exists() else qs

    def filter_day(self, qs, name, raw):
        codes = [v.capitalize()[:3].upper() for v in parse_str_list(raw)]
        if not codes:
            return qs
        q = Q()
        for c in codes:
            q |= Q(days__name__startswith=c)
        filtered = qs.filter(q).distinct()
        return filtered if filtered.exists() else qs

    def filter_queryset(self, qs):
        params = self.request.query_params

        # 1) Many-to-many first: categories and centers
        qs = self.filter_category(qs, 'category_ids',     params.get('category_ids'))
        qs = self.filter_center(qs, 'edu_center_ids',   params.get('edu_center_ids'))

        # 2) Numeric ranges
        for name in (
            'price_min', 'price_max',
            'total_places_min', 'total_places_max'
        ):
            raw = params.get(name)
            if raw not in (None, '', []):
                qs = self.filters[name].filter(qs, raw)

        # 3) Multi-value teacher_gender
        raw_g = params.get('teacher_gender')
        if raw_g not in (None, '', []):
            qs = self.filter_gender(qs, 'teacher_gender', raw_g)

        # 4) Day filter
        raw_d = params.get('day')
        if raw_d not in (None, '', []):
            qs = self.filter_day(qs, 'day', raw_d)

        return qs.distinct()


class EventFilter(filters.FilterSet):
    category_ids = filters.CharFilter(method="filter_category")
    edu_center_ids = filters.CharFilter(method="filter_center")
    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Event
        fields = []

    def filter_category(self, qs, name, raw):
        ids = parse_int_list(raw)
        if not ids:
            return qs
        filtered = qs.filter(categories__id__in=ids)
        return filtered if filtered.exists() else qs

    def filter_center(self, qs, name, raw):
        ids = parse_int_list(raw)
        if not ids:
            return qs
        filtered = qs.filter(edu_center__id__in=ids)
        return filtered if filtered.exists() else qs

    def filter_queryset(self, qs):
        params = self.request.query_params

        qs = self.filter_category(qs, 'category_ids',     params.get('category_ids'))
        qs = self.filter_center(qs, 'edu_center_ids',   params.get('edu_center_ids'))

        for name in ('start_date', 'end_date'):
            raw = params.get(name)
            if raw not in (None, '', []):
                candidate = self.filters[name].filter(qs, raw)
                if candidate.exists():
                    qs = candidate

        return qs.distinct()
