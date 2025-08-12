"""
URL configuration for cbms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from budget import views as v

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', v.root_view, name='root'),
    path('home/', v.home, name='home'),
    path('login/', v.login_view, name='login'),
    path('signup/', v.signup_view, name='signup'),
    path('logout/', v.logout_view, name='logout'),
    path('add-people/', v.add_people, name='add_people'),
    path('delete-person/<int:person_id>/', v.delete_person, name='delete_person'),
    path('add-expense/', v.add_expense, name='add_expense'),
    path('add-income/', v.add_income, name='add_income'),
    path('account-analysis/', v.account_analysis, name='account_analysis'),
    path('expense/<int:expense_id>/', v.expense_detail, name='expense_detail'),
    path('download-csv/', v.download_csv, name='download_csv'),
    path('balance-sheet/', v.balance_sheet, name='balance_sheet'),
    path('profit-loss-summary/', v.profit_loss_summary, name='profit_loss_summary'),
]
