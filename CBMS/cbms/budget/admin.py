from django.contrib import admin
from .models import Person, Expense, Income

# Register your models here.
admin.site.register(Person)
admin.site.register(Expense)
admin.site.register(Income)