from django_filters.rest_framework import FilterSet
from django.db.models import Q
from main.models import Course

class CourseFilter(FilterSet):
    class Meta:
        model = Course
        fields = {
            'price': ['gte', 'lte'],
            'total_places': ['gte', 'lte'],
            'teacher__gender': ['exact'],
            'branch__edu_center__id': ['exact'],
            'branch__edu_center__name': ['icontains'],
            'category': ['exact'],
        }

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.q = Q()

        if data:
            if data.get('teacher_gender'):
                self.q |= Q(teacher__gender__iexact=data['teacher_gender'])
            if data.get('edu_center'):
                self.q |= Q(branch__edu_center__id=data['edu_center'])
            if data.get('edu_center_name'):
                self.q |= Q(branch__edu_center__name__icontains=data['edu_center_name'])
            if data.get('price_min'):
                self.q |= Q(price__gte=data['price_min'])
            if data.get('price_max'):
                self.q |= Q(price__lte=data['price_max'])
            if data.get('total_places_min'):
                self.q |= Q(total_places__gte=data['total_places_min'])
            if data.get('total_places_max'):
                self.q |= Q(total_places__lte=data['total_places_max'])
            if data.get('category'):
                self.q |= Q(category__id=data['category'])

    def filter_queryset(self, queryset):
        if self.q:
            return queryset.filter(self.q)
        return queryset
