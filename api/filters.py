from django.db.models import Q
import django_filters
from django_filters import rest_framework as filters
from main.models import Course, Day, Event


class DayNameInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    day parametri ro'yxat (['Mon','Tue']) yoki vergul bilan ajratilgan
    string ("Mon,Tue") kelsa ham qabul qiladi.
    """

    def filter(self, qs, value):
        # value: list yoki string
        if not value:
            return qs
        if isinstance(value, (list, tuple)):
            parts = []
            for elem in value:
                if "," in elem:
                    parts += [p.strip() for p in elem.split(",")]
                else:
                    parts.append(elem)
            value_list = parts
        else:
            value_list = [p.strip() for p in value.split(",")]
        q = Q()
        for val in value_list:
            code = val.capitalize()[:3]
            matched_days = Day.objects.filter(name__startswith=code.upper())
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
    category_id = filters.BaseInFilter(field_name="category__id", lookup_expr="in")
    day = DayNameInFilter(method="filter", field_name="days__name")

    class Meta:
        model = Course
        fields = [
            "price_min", "price_max",
            "total_places_min", "total_places_max",
            "teacher_gender",
            "edu_center_id",
            "category_id",
            "day",
        ]

    def filter_by_edu_center(self, qs, name, value):
        return qs.filter(branch__edu_center__id=value)


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class EventFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")
    edu_center_id = NumberInFilter(field_name="edu_center__id", lookup_expr="in")
    category_id = NumberInFilter(field_name="categories__id", lookup_expr="in")

    class Meta:
        model = Event
        fields = [
            "start_date",
            "end_date",
            "edu_center_id",
            "category_id",
        ]
