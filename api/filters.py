from django_filters.rest_framework import FilterSet, filters
from main.models import Course, Day, Event
from django.db.models import Q
import django_filters


class DayNameInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class CourseFilter(FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="price", lookup_expr="lte")
    total_places_min = filters.NumberFilter(
        field_name="total_places", lookup_expr="gte")
    total_places_max = filters.NumberFilter(
        field_name="total_places", lookup_expr="lte")
    teacher_gender = filters.CharFilter(
        field_name="teacher__gender", lookup_expr="iexact")
    edu_center = filters.CharFilter(method='filter_by_edu_center')
    category = filters.BaseInFilter(
        field_name="category__id", lookup_expr="in")
    day = DayNameInFilter(method='filter_by_days')

    class Meta:
        model = Course
        fields = ['price', 'total_places', 'teacher__gender',
                  'branch__edu_center__id', 'category']

    def filter_by_edu_center(self, queryset, name, value):
        return queryset.filter(branch__edu_center__id=value)

    def filter_by_days(self, queryset, name, value_list):
        q = Q()
        for val in value_list:
            val = val.strip().capitalize()[:3]
            matched_days = Day.objects.filter(name__startswith=val.upper())
            q |= Q(days__in=matched_days)
        return queryset.filter(q).distinct()


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class EventFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name='date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    edu_center_id = NumberInFilter(
        field_name='edu_center__id', lookup_expr='in')
    category = NumberInFilter(
        field_name='categories__id', lookup_expr='in')

    class Meta:
        model = Event
        fields = ['start_date', 'end_date', 'edu_center_id', 'category']
