import json
from django.db.models import Q
from django_filters import rest_framework as filters
from main.models import Course, Event, Day


def parse_int_list(raw):
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
    if s.startswith('[') and s.endswith(']'):
        try:
            arr = json.loads(s)
            return [int(x) for x in arr]
        except Exception:
            s = s[1:-1]
    return [int(x) for x in s.split(',') if x.strip().isdigit()]


def parse_str_list(raw):
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw if x]
    s = raw.strip()
    if s.startswith('[') and s.endswith(']'):
        try:
            arr = json.loads(s)
            return [str(x) for x in arr]
        except Exception:
            s = s[1:-1]
    return [x.strip() for x in s.split(',') if x.strip()]


class CourseFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    total_places_min = filters.NumberFilter(
        field_name="total_places", lookup_expr="gte")
    total_places_max = filters.NumberFilter(
        field_name="total_places", lookup_expr="lte")
    teacher_gender = filters.CharFilter(
        field_name="teacher__gender", lookup_expr="iexact")

    # hammasi CharFilter qilib qo'ydik, .filter_<name> metodlari bilan
    category_ids = filters.CharFilter(method="filter_category")
    edu_center_ids = filters.CharFilter(method="filter_center")
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

        # 1) Category
        qs = self.filter_category(qs, 'category_ids', params.get('category_ids'))

        # 2) Edu center
        qs = self.filter_center(qs, 'edu_center_ids', params.get('edu_center_ids'))

        # 3) price_min, price_max, total_places_min, total_places_max, teacher_gender
        for name in (
            'price_min', 'price_max',
            'total_places_min', 'total_places_max',
            'teacher_gender'
        ):
            raw = params.get(name)
            if raw not in (None, '', []):
                filt = self.filters[name]
                candidate = filt.filter(qs, raw)
                if candidate.exists():
                    qs = candidate

        # 4) day (oxirgi bo‘lsa ham bo‘ladi)
        raw_day = params.get('day')
        if raw_day not in (None, '', []):
            candidate = self.filter_day(qs, 'day', raw_day)
            if candidate.exists():
                qs = candidate

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

        qs = self.filter_category(qs, 'category_ids', params.get('category_ids'))
        qs = self.filter_center(qs, 'edu_center_ids', params.get('edu_center_ids'))

        for name in ('start_date', 'end_date'):
            raw = params.get(name)
            if raw:
                candidate = self.filters[name].filter(qs, raw)
                if candidate.exists():
                    qs = candidate

        return qs.distinct()
