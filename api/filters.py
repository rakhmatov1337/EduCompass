from django.db.models import Q
import django_filters
from django_filters import rest_framework as filters
from main.models import Course, Day, Event


class DayNameInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Accepts list of day strings or comma-separated string and filters by matching Day names.
    """

    def filter(self, qs, value):
        if not value:
            return qs
        values = []
        # Handle list inputs
        if isinstance(value, (list, tuple)):
            for v in value:
                # Split comma-separated strings in list
                if isinstance(v, str) and "," in v:
                    values.extend([item.strip() for item in v.split(",")])
                else:
                    values.append(v)
        else:
            values = [item.strip() for item in value.split(",")]
        # Normalize codes to first 3 uppercase letters
        codes = [val.capitalize()[:3].upper() for val in values if val]
        q = Q()
        for code in codes:
            matched_days = Day.objects.filter(name__startswith=code)
            q |= Q(days__in=matched_days)
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
    category_ids = filters.BaseInFilter(field_name="category__id", lookup_expr="in")
    day = DayNameInFilter(field_name="days__name")

    class Meta:
        model = Course
        fields = [] 

    def filter_by_edu_center(self, qs, name, value):
        return qs.filter(branch__edu_center__id=value)


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class EventFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")
    edu_center_id = NumberInFilter(field_name="edu_center__id", lookup_expr="in")
    category_ids = NumberInFilter(field_name="categories__id", lookup_expr="in")

    class Meta:
        model = Event
        fields = []  
