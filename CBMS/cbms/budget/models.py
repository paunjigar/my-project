from django.db import models
from django.contrib.auth.models import User

class Person(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='persons')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    num = models.IntegerField(default=0)
    job_post = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['user', 'email']  # Email should be unique per user
    
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('marketing', 'Marketing'),
        ('salaries', 'Salaries'),
        ('utilities', 'Utilities'),
        ('rent', 'Rent'),
        ('equipment', 'Equipment'),
        ('travel', 'Travel'),
        ('food', 'Food & Entertainment'),
        ('other', 'Other'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('digital_wallet', 'Digital Wallet'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    vendor = models.CharField(max_length=200, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)

class Income(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('digital_wallet', 'Digital Wallet'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes')
    person = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank_transfer')
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)


    