from django.db.models import Q
from django_filters import rest_framework as filters
from main.models import Course, Event


class DayNameInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Accepts list of day strings or comma-separated string and filters by matching Day names.
    """

    def filter(self, qs, value):
        if not value:
            return qs
        if isinstance(value, (list, tuple)):
            raw = []
            for v in value:
                if isinstance(v, str) and "," in v:
                    raw += [x.strip() for x in v.split(",")]
                else:
                    raw.append(v)
        else:
            raw = [x.strip() for x in value.split(",")]

        codes = [v.capitalize()[:3].upper() for v in raw if v]
        q = Q()
        for code in codes:
            q |= Q(days__name__startswith=code)
        return qs.filter(q).distinct()


class CourseFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price",        lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price",        lookup_expr="lte")
    total_places_min = filters.NumberFilter(
        field_name="total_places", lookup_expr="gte")
    total_places_max = filters.NumberFilter(
        field_name="total_places", lookup_expr="lte")
    teacher_gender = filters.CharFilter(
        field_name="teacher__gender", lookup_expr="iexact")
    edu_center_id = filters.NumberFilter(method="filter_by_edu_center")
    day = DayNameInFilter(field_name="days__name")
    category_ids = filters.BaseInFilter(field_name="category__id", lookup_expr="in")

    class Meta:
        model = Course
        fields = []

    def filter_by_edu_center(self, qs, name, value):
        return qs.filter(branch__edu_center__id=value)

    def filter_queryset(self, queryset):
        data = self.form.cleaned_data
        qs = queryset

        # 1) Primary: category_ids
        cat_vals = data.get('category_ids')
        if cat_vals:
            qs = qs.filter(category__id__in=cat_vals)

        # 2) edu_center_id
        center = data.get('edu_center_id')
        if center:
            qs = qs.filter(branch__edu_center__id=center)

        # 3) All the rest in declaration order
        for name, filter_obj in self.filters.items():
            if name in ('category_ids', 'edu_center_id'):
                continue

            val = data.get(name)
            if val not in (None, [], ''):
                qs = filter_obj.filter(qs, val)

        return qs.distinct()


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    """Just a plain “in” filter for numbers."""
    pass


class EventFilter(filters.FilterSet):
    category_ids = NumberInFilter(field_name="categories__id", lookup_expr="in")
    edu_center_ids = NumberInFilter(field_name="edu_center__id", lookup_expr="in")
    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Event
        fields = []

    def filter_queryset(self, queryset):
        data = self.form.cleaned_data
        qs = queryset

        # 1) categories first
        cats = data.get('category_ids')
        if cats:
            qs = qs.filter(categories__id__in=cats)

        # 2) edu_center_ids next
        centers = data.get('edu_center_ids')
        if centers:
            qs = qs.filter(edu_center__id__in=centers)

        # 3) then dates
        for name in ('start_date', 'end_date'):
            val = data.get(name)
            if val:
                qs = self.filters[name].filter(qs, val)

        return qs.distinct()
