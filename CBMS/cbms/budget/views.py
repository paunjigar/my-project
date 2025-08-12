from django.shortcuts import render, redirect, get_object_or_404
from .models import Person, Expense, Income
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import json
from datetime import datetime, timedelta
import calendar
import csv
from django.conf import settings
import os

import pandas as pd
from sklearn.linear_model import LinearRegression



# Create your views here.
def root_view(request):
    """Root view that redirects to login if not authenticated, or home if authenticated"""
    if request.user.is_authenticated:
        return redirect('home')
    else:
        return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error = 'Username or password do not match.'
    return render(request, 'login.html', {'error': error})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if not username or not password or not password2:
            error = 'Please fill all fields.'
        elif password != password2:
            error = 'Passwords do not match.'
        elif User.objects.filter(username=username).exists():
            error = 'Username already exists.'
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('home')
    return render(request, 'signup.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('root')


@login_required(login_url='login')
def home(request):
    # Get current month and year
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Basic stats
    total_people = Person.objects.filter(user=request.user).count()
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    company_balance = total_income - total_expense
    
    # Monthly data for current month
    current_month_income = Income.objects.filter(
        user=request.user,
        date__year=current_year,
        date__month=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    current_month_expense = Expense.objects.filter(
        user=request.user,
        date__year=current_year,
        date__month=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    current_month_balance = current_month_income - current_month_expense
    

    
    # Get last 6 months of data for trends
    months_data = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30*i)
        month_year = month_date.year
        month_month = month_date.month
        
        month_income = Income.objects.filter(
            user=request.user,
            date__year=month_year,
            date__month=month_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        month_expense = Expense.objects.filter(
            user=request.user,
            date__year=month_year,
            date__month=month_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        month_name = calendar.month_name[month_month][:3]
        months_data.append({
            'month': f"{month_name} {month_year}",
            'income': float(month_income),
            'expense': float(month_expense),
            'balance': float(month_income - month_expense)
        })
    

    
    # Recent transactions (last 5)
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-date')[:5]
    recent_incomes = Income.objects.filter(user=request.user).order_by('-date')[:5]
    
    context = {
        'total_people': total_people,
        'total_income': total_income,
        'total_expense': total_expense,
        'company_balance': company_balance,
        'current_month_income': current_month_income,
        'current_month_expense': current_month_expense,
        'current_month_balance': current_month_balance,
        'current_month': now,
        'months_data': json.dumps(months_data),
        'recent_expenses': recent_expenses,
        'recent_incomes': recent_incomes,
    }
    
    return render(request, 'home.html', context)

    

# Placeholder view for account analysis

@login_required(login_url='login')
def add_people(request):
    people = Person.objects.filter(user=request.user)
    error = None
    success = False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        num = request.POST.get('mobile')
        job_post = request.POST.get('job_post')
        if name and email and job_post and num:
            if Person.objects.filter(user=request.user, email=email).exists():
                error = 'A person with this email already exists.'
            else:
                Person.objects.create(user=request.user, name=name, email=email, job_post=job_post, num=num)
                success = True
        else:
            error = 'Please fill all fields.'
        return render(request, 'add_people.html', {'people': people, 'error': error, 'success': success})
    return render(request, 'add_people.html', {'people': people})

@login_required(login_url='login')
def delete_person(request, person_id):
    if request.method == 'POST':
        person = get_object_or_404(Person, id=person_id, user=request.user)
        person.delete()
        return render(request, 'add_people.html', {'people': Person.objects.filter(user=request.user), 'success': True, 'delete_message': 'Person deleted successfully.'})
    return redirect('add_people')

@login_required(login_url='login')
def add_expense(request):
    people = Person.objects.filter(user=request.user)
    if request.method == 'POST':
        person_name = request.POST.get('name')
        amount = request.POST.get('amount')
        category = request.POST.get('category', 'other')
        vendor = request.POST.get('vendor', '')
        payment_method = request.POST.get('payment_method', 'cash')
        date = request.POST.get('date')
        notes = request.POST.get('notes', '')
        if person_name and amount and date:
            # Calculate current balance
            total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0  #to combine multiple values into a single summary value
            total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
            current_balance = total_income - total_expense
            
            # Convert amount to decimal for comparison
            try:
                expense_amount = float(amount)
                if expense_amount > current_balance:
                    return render(request, 'add_expense.html', {
                        'people': people, 
                        'error': f'Insufficient balance. Your current balance is ₹{current_balance:.2f}, but you are trying to spend ₹{expense_amount:.2f}.'
                    })
            except ValueError:
                return render(request, 'add_expense.html', {
                    'people': people, 
                    'error': 'Please enter a valid amount.'
                })
            
            # Get or create the Person object by name
            try:
                person, created = Person.objects.get_or_create(
                    user=request.user,
                    name=person_name,
                    defaults={
                        'email': f'{person_name.lower().replace(" ", ".")}@company.com',
                        'job_post': 'Employee',
                        'num': 0
                    }
                )
                Expense.objects.create(
                    user=request.user, 
                    person=person, 
                    amount=amount, 
                    category=category,
                    vendor=vendor,
                    payment_method=payment_method,
                    date=date,
                    notes=notes
                )
                return render(request, 'add_expense.html', {'people': people, 'success': True})
            except Exception as e:
                return render(request, 'add_expense.html', {'people': people, 'error': f'Error creating expense: {str(e)}'})
    return render(request, 'add_expense.html', {'people': people})

@login_required(login_url='login')
def add_income(request):
    if request.method == 'POST':
        person=request.POST.get('person_name')
        amount=request.POST.get('amount')
        source_name=request.POST.get('source_name')
        category=request.POST.get('category', '')
        payment_method=request.POST.get('payment_method', 'bank_transfer')
        date=request.POST.get('date')
        notes=request.POST.get('notes', '')
        if person and amount and source_name and date:
            try:
                Income.objects.create(
                    user=request.user, 
                    person=person, 
                    amount=amount, 
                    source_name=source_name,
                    category=category,
                    payment_method=payment_method,
                    date=date,
                    notes=notes
                )
                return render(request, 'add_income.html', {'people': Person.objects.filter(user=request.user), 'success': True})
            except Exception as e:
                return render(request, 'add_income.html', {'people': Person.objects.filter(user=request.user), 'error': f'Error adding income: {str(e)}'})
        else:
            return render(request, 'add_income.html', {'people': Person.objects.filter(user=request.user), 'error': 'Please fill all required fields.'})
    return render(request, 'add_income.html', {'people': Person.objects.filter(user=request.user)})



@login_required(login_url='login')
def account_analysis(request):
    from datetime import datetime
    
    # Get the selected month from query parameters
    selected_month = request.GET.get('month')
    
    # Generate months list for the dropdown
    months = []
    current_year = datetime.now().year
    for month_num in range(1, 13):
        month_date = datetime(current_year, month_num, 1)
        month_value = f"{current_year}-{month_num:02d}"
        month_label = month_date.strftime("%B %Y")
        months.append({
            'value': month_value,
            'label': month_label
        })
    
    if selected_month:
        # Parse the selected month
        year, month = selected_month.split('-')
        year, month = int(year), int(month)
        
        # Get the month label for display
        selected_month_label = datetime(year, month, 1).strftime("%B %Y")
        
        # Filter expenses for the selected month and current user
        expenses = Expense.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).order_by('date')
        
        # Filter income for the selected month and current user
        incomes = Income.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).order_by('date')
        
        # Calculate totals
        total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
        net_balance = total_income - total_expense
        
        context = {
            'months': months,
            'selected_month': selected_month,
            'selected_month_label': selected_month_label,
            'expenses': expenses,
            'incomes': incomes,
            'total_expense': total_expense,
            'total_income': total_income,
            'net_balance': net_balance,
        }
    else:
        context = {
            'months': months,
        }
    # # Predict future expenses and income
    # predicted_expense, predicted_income, required_income = predict_expense_and_income()
    # context['predicted_expense'] = predicted_expense
    # context['predicted_income'] = predicted_income
    # context['required_income'] = required_income
    # # Render the template with context
    return render(request, 'account_analysis.html', context)



# def predict_expense_and_income():
#     # Load CSVs
#     expense_path = os.path.join(settings.BASE_DIR, 'budget', 'static', 'csv', 'expenses.csv')
#     income_path = os.path.join(settings.BASE_DIR, 'budget', 'static', 'csv', 'incomes.csv')

#     expenses = pd.read_csv(expense_path)
#     incomes = pd.read_csv(income_path)

#     def preprocess(df, value_col):
#         df['date'] = pd.to_datetime(df['date'])
#         df['month'] = df['date'].dt.month
#         df['year'] = df['date'].dt.year
#         monthly = df.groupby(['year', 'month'])[value_col].sum().reset_index()
#         return monthly

#     def predict_next(monthly_df, value_col):
#         model = LinearRegression()
#         X = monthly_df[['year', 'month']]
#         y = monthly_df[value_col]
#         model.fit(X, y)
#         last = monthly_df.iloc[-1]
#         next_month = (last['month'] % 12) + 1
#         next_year = last['year'] + (1 if last['month'] == 12 else 0)
#         return round(model.predict([[next_year, next_month]])[0], 2)

#     expense_monthly = preprocess(expenses, 'amount')
#     income_monthly = preprocess(incomes, 'amount')

#     predicted_expense = predict_next(expense_monthly, 'amount')
#     predicted_income = predict_next(income_monthly, 'amount')

#     required_income = max(predicted_income, round(predicted_expense * 150, 2))

#     return predicted_expense, predicted_income, required_income



@login_required(login_url='login')
def expense_detail(request, expense_id):
    """View detailed information about a specific expense"""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    return render(request, 'expense_detail.html', {'expense': expense})

@login_required(login_url='login')
def download_csv(request):
    """Download CSV report for the selected month"""
    selected_month = request.GET.get('month')
    report_type = request.GET.get('type', 'expenses')  # expenses, income, or all
    
    if not selected_month:
        return HttpResponse("Please select a month", status=400)
    
    # Parse the selected month
    year, month = selected_month.split('-')
    year, month = int(year), int(month)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cbms_report_{year}_{month:02d}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'expenses':
        # Export expenses
        expenses = Expense.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).order_by('date')
        
        writer.writerow(['Expense Report', f'{calendar.month_name[month]} {year}'])
        writer.writerow([])
        writer.writerow(['Date', 'Person', 'Category', 'Vendor', 'Payment Method', 'Amount', 'Notes'])
        
        total = 0
        for expense in expenses:
            writer.writerow([
                expense.date.strftime('%Y-%m-%d'),
                expense.person.name,
                expense.get_category_display(),
                expense.vendor or '',
                expense.get_payment_method_display(),
                expense.amount,
                expense.notes or ''
            ])
            total += expense.amount
        
        writer.writerow([])
        writer.writerow(['Total Expenses', '', '', '', '', total])
        
    elif report_type == 'income':
        # Export income
        incomes = Income.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).order_by('date')
        
        writer.writerow(['Income Report', f'{calendar.month_name[month]} {year}'])
        writer.writerow([])
        writer.writerow(['Date', 'Person', 'Source', 'Amount'])
        
        total = 0
        for income in incomes:
            writer.writerow([
                income.date.strftime('%Y-%m-%d'),
                income.person,
                income.source_name,
                income.amount
            ])
            total += income.amount
        
        writer.writerow([])
        writer.writerow(['Total Income', '', '', total])
        
    else:  # all
        # Export both expenses and income
        expenses = Expense.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).order_by('date')
        
        incomes = Income.objects.filter(
            user=request.user,
            date__year=year,
            date__month=month
        ).order_by('date')
        
        writer.writerow(['CBMS Financial Report', f'{calendar.month_name[month]} {year}'])
        writer.writerow([])
        
        # Expenses section
        writer.writerow(['EXPENSES'])
        writer.writerow(['Date', 'Person', 'Category', 'Vendor', 'Payment Method', 'Amount', 'Notes'])
        
        expense_total = 0
        for expense in expenses:
            writer.writerow([
                expense.date.strftime('%Y-%m-%d'),
                expense.person.name,
                expense.get_category_display(),
                expense.vendor or '',
                expense.get_payment_method_display(),
                expense.amount,
                expense.notes or ''
            ])
            expense_total += expense.amount
        
        writer.writerow(['Total Expenses', '', '', '', '', expense_total])
        writer.writerow([])
        
        # Income section
        writer.writerow(['INCOME'])
        writer.writerow(['Date', 'Person', 'Source', 'Amount'])
        
        income_total = 0
        for income in incomes:
            writer.writerow([
                income.date.strftime('%Y-%m-%d'),
                income.person,
                income.source_name,
                income.amount
            ])
            income_total += income.amount
        
        writer.writerow(['Total Income', '', '', income_total])
        writer.writerow([])
        
        # Summary
        net_balance = income_total - expense_total
        writer.writerow(['SUMMARY'])
        writer.writerow(['Total Income', income_total])
        writer.writerow(['Total Expenses', expense_total])
        writer.writerow(['Net Balance', net_balance])
    
    return response

@login_required(login_url='login')
def balance_sheet(request):
    """Generate balance sheet report"""
    selected_month = request.GET.get('month')
    
    if not selected_month:
        return HttpResponse("Please select a month", status=400)
    
    # Parse the selected month
    year, month = selected_month.split('-')
    year, month = int(year), int(month)
    
    # Get data for the selected month
    expenses = Expense.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )
    
    incomes = Income.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_income - total_expenses
    
    # Get category breakdown
    category_expenses = []
    for cat in expenses.values('category').annotate(total=Sum('amount')).order_by('-total'):
        # Handle custom category names that might not be in CATEGORY_CHOICES
        try:
            category_display = dict(Expense.CATEGORY_CHOICES)[cat['category']]
        except KeyError:
            category_display = cat['category'].title()  # Use the custom name as-is
        category_expenses.append({
            'category': cat['category'],
            'category_display': category_display,
            'total': cat['total']
        })
    
    # Get payment method breakdown
    payment_method_expenses = []
    for payment in expenses.values('payment_method').annotate(total=Sum('amount')).order_by('-total'):
        # Handle custom payment method names that might not be in PAYMENT_METHOD_CHOICES
        try:
            payment_display = dict(Expense.PAYMENT_METHOD_CHOICES)[payment['payment_method']]
        except KeyError:
            payment_display = payment['payment_method'].title()  # Use the custom name as-is
        payment_method_expenses.append({
            'payment_method': payment['payment_method'],
            'payment_display': payment_display,
            'total': payment['total']
        })
    
    context = {
        'selected_month': f"{calendar.month_name[month]} {year}",
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'category_expenses': category_expenses,
        'payment_method_expenses': payment_method_expenses,
        'expenses': expenses,
        'incomes': incomes,
        'user': request.user
    }
    
    return render(request, 'balance_sheet.html', context)

@login_required(login_url='login')
def profit_loss_summary(request):
    """Generate profit/loss summary report"""
    selected_month = request.GET.get('month')
    
    if not selected_month:
        return HttpResponse("Please select a month", status=400)
    
    # Parse the selected month
    year, month = selected_month.split('-')
    year, month = int(year), int(month)
    
    # Get data for the selected month
    expenses = Expense.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )
    
    incomes = Income.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    net_profit = total_income - total_expenses
    
    # Get category breakdown for expenses with percentages
    category_expenses = []
    if total_expenses > 0:
        for cat in expenses.values('category').annotate(total=Sum('amount')).order_by('-total'):
            percentage = (cat['total'] / total_expenses * 100) if total_expenses > 0 else 0
            # Handle custom category names that might not be in CATEGORY_CHOICES
            try:
                category_display = dict(Expense.CATEGORY_CHOICES)[cat['category']]
            except KeyError:
                category_display = cat['category'].title()  # Use the custom name as-is
            category_expenses.append({
                'category': cat['category'],
                'category_display': category_display,
                'total': cat['total'],
                'percentage': round(percentage, 1)
            })
    
    # Get income sources breakdown with percentages
    income_sources = []
    if total_income > 0:
        for source in incomes.values('source_name').annotate(total=Sum('amount')).order_by('-total'):
            percentage = (source['total'] / total_income * 100) if total_income > 0 else 0
            income_sources.append({
                'source_name': source['source_name'],
                'total': source['total'],
                'percentage': round(percentage, 1)
            })
    
    # Calculate percentages
    expense_percentage = (total_expenses / total_income * 100) if total_income > 0 else 0
    profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
    
    context = {
        'selected_month': f"{calendar.month_name[month]} {year}",
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'expense_percentage': expense_percentage,
        'profit_margin': profit_margin,
        'category_expenses': category_expenses,
        'income_sources': income_sources,
        'expenses': expenses,
        'incomes': incomes,
        'user': request.user
    }
    
    return render(request, 'profit_loss_summary.html', context)


