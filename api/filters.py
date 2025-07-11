from django.db.models import Q
import django_filters
from django_filters import rest_framework as filters
from main.models import Course, Day


class DayNameInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Accepts list of day strings or comma-separated string and filters by matching Day names.
    """
    def filter(self, qs, name, value):
        if not value:
            return qs
        if isinstance(value, (list, tuple)):
            raw = []
            for v in value:
                if isinstance(v, str) and ',' in v:
                    raw += [x.strip() for x in v.split(',')]
                else:
                    raw.append(v)
        else:
            raw = [x.strip() for x in value.split(',')]
        codes = [v.capitalize()[:3].upper() for v in raw if v]
        day_q = Q()
        for code in codes:
            day_q |= Q(days__name__startswith=code)
        return qs.filter(day_q).distinct()


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
        """
        1. Pull out category_ids and apply.
        2. Loop through the rest of the declared filters in definition order.
        """
        data = self.form.cleaned_data
        qs = queryset
        cat_vals = data.get('category_ids')
        if cat_vals:
            qs = qs.filter(category__id__in=cat_vals)
        for name, filter_obj in self.filters.items():
            if name == 'category_ids':
                continue

            val = data.get(name)
            if val is not None and val != [] and val != '':
                qs = filter_obj.filter(qs, name, val)

        return qs.distinct()
