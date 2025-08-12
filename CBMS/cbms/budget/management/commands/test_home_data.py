from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from budget.models import Income, Expense, Person
from datetime import datetime
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Test the home page data calculation'

    def handle(self, *args, **options):
        # Get current month and year
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        self.stdout.write(f"Current month/year: {current_month}/{current_year}")
        
        # Get all users
        users = User.objects.all()
        
        for user in users:
            self.stdout.write(f"\n--- User: {user.username} ---")
            
            # Basic stats
            total_people = Person.objects.filter(user=user).count()
            total_income = Income.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
            total_expense = Expense.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
            
            self.stdout.write(f"Total people: {total_people}")
            self.stdout.write(f"Total income: {total_income}")
            self.stdout.write(f"Total expense: {total_expense}")
            
            # Monthly data for current month
            current_month_income = Income.objects.filter(
                user=user,
                date__year=current_year,
                date__month=current_month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            current_month_expense = Expense.objects.filter(
                user=user,
                date__year=current_year,
                date__month=current_month
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            current_month_balance = current_month_income - current_month_expense
            
            self.stdout.write(f"Current month income: {current_month_income}")
            self.stdout.write(f"Current month expense: {current_month_expense}")
            self.stdout.write(f"Current month balance: {current_month_balance}")
            
            # Check if there are any income/expense records
            total_income_records = Income.objects.filter(user=user).count()
            total_expense_records = Expense.objects.filter(user=user).count()
            self.stdout.write(f"Total income records: {total_income_records}")
            self.stdout.write(f"Total expense records: {total_expense_records}")
            
            # Check records for current month
            current_month_income_records = Income.objects.filter(
                user=user,
                date__year=current_year,
                date__month=current_month
            ).count()
            current_month_expense_records = Expense.objects.filter(
                user=user,
                date__year=current_year,
                date__month=current_month
            ).count()
            self.stdout.write(f"Current month income records: {current_month_income_records}")
            self.stdout.write(f"Current month expense records: {current_month_expense_records}")
            
            # Show some sample records
            if current_month_income_records > 0:
                self.stdout.write("Sample income records for current month:")
                for income in Income.objects.filter(
                    user=user,
                    date__year=current_year,
                    date__month=current_month
                )[:3]:
                    self.stdout.write(f"  - {income.date}: {income.amount} ({income.person})")
            
            if current_month_expense_records > 0:
                self.stdout.write("Sample expense records for current month:")
                for expense in Expense.objects.filter(
                    user=user,
                    date__year=current_year,
                    date__month=current_month
                )[:3]:
                    self.stdout.write(f"  - {expense.date}: {expense.amount} ({expense.person.name})") 