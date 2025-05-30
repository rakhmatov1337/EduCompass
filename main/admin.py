from django.contrib import admin

from .models import EduType, Category, Day, Teacher, EducationCenter, Branch, Course, Level
# Register your models here.

admin.site.register(EduType)
admin.site.register(Category)
admin.site.register(Day)
admin.site.register(Teacher)
admin.site.register(EducationCenter)
admin.site.register(Branch)
admin.site.register(Course)
admin.site.register(Level)
