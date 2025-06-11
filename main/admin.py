from django.contrib import admin

from .models import (Branch, Category, Course, Day, EducationCenter, EduType,
                     Enrollment, Event, Level, Teacher)

# Register your models here.

admin.site.register(EduType)
admin.site.register(Category)
admin.site.register(Day)
admin.site.register(Teacher)
admin.site.register(EducationCenter)
admin.site.register(Branch)
admin.site.register(Course)
admin.site.register(Level)
admin.site.register(Event)
admin.site.register(Enrollment)
