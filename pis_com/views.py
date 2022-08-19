# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.views.generic import TemplateView, RedirectView, UpdateView
from django.views.generic import FormView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render
from pis_com.models import Customer,FeedBack
from pis_com.models import AdminConfiguration
from pis_com.forms import CustomerForm,FeedBackForm

from pis_retailer.models import RetailerUser
from pis_retailer.forms import RetailerForm, RetailerUserForm
import json
import datetime
# from rest_framework.decorators import api_view

from calendar import monthrange
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from django.views.generic import View
from django.http import JsonResponse
from django.db.models import Sum

from pis_product.models import StockOut

class LoginView(FormView):
    template_name = 'login.html'
    form_class = auth_forms.AuthenticationForm
    
    def dispatch(self, request, *args, **kwargs):

        if self.request.user.is_authenticated:
            if (
                self.request.user.retailer_user.role_type ==
                self.request.user.retailer_user.ROLE_TYPE_LEDGER_VIEW
            ):
                return HttpResponseRedirect(
                    reverse('ledger:customer_ledger_list'))

            return HttpResponseRedirect(reverse('index'))

        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)

        return HttpResponseRedirect(reverse('index'))
    
    def form_invalid(self, form):
        return super(LoginView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        try:
            admin_config = AdminConfiguration.objects.get(id=1)
            context.update({
                'config': admin_config
            })
        except AdminConfiguration.DoesNotExist:
            pass
        return context


class LogoutView(RedirectView):

    def dispatch(self, request, *args, **kwargs):
        auth_logout(self.request)
        return super(LogoutView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('login'))


class RegisterView(FormView):
    form_class = auth_forms.UserCreationForm
    template_name = 'register.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('index'))

        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # register new user in the system
        user = form.save()

        # Create Retailer
        retailer_form_kwargs = {
            'name': (
                '%s %s' % (user.first_name, user.last_name) if
                user.first_name else user.username),
            'slug': (
                '%s-%s' % (user.first_name, user.last_name) if
                user.first_name else user.username)
        }
        retailer_form = RetailerForm(retailer_form_kwargs)
        if retailer_form.is_valid():
            retailer = retailer_form.save()

            retailer_user_kwargs = {
                'retailer': retailer.id,
                'user': user.id,
                'role_type': RetailerUser.ROLE_TYPE_LEDGER_VIEW
            }

            retailer_user_form = RetailerUserForm(retailer_user_kwargs)
            if retailer_user_form.is_valid():
                retailer_user_form.save()

        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        auth_user = authenticate(username=username, password=raw_password)
        auth_login(self.request, auth_user)

        return HttpResponseRedirect(reverse('ledger:customer_ledger_list'))

    def form_invalid(self, form):
        return super(RegisterView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(RegisterView, self).get_context_data(**kwargs)
        if self.request.POST:
            context.update({
                'username': self.request.POST.get('username'),
                'password1': self.request.POST.get('password1'),
                'password2': self.request.POST.get('password2')
            })

        return context


class HomePageView(TemplateView):
    template_name = 'index.html'

    def dispatch(self, request, *args, **kwargs):
        a = self.request
        print(a)

        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        else:

            if self.request.user.retailer_user:
                if (
                    self.request.user.retailer_user.role_type ==
                        self.request.user.retailer_user.ROLE_TYPE_SALESMAN
                ):
                    return HttpResponseRedirect(reverse('sales:invoice_list'))
            if self.request.user.retailer_user:
                if (
                        self.request.user.retailer_user.role_type ==
                        self.request.user.retailer_user.ROLE_TYPE_DATA_ENTRY_USER
                ):
                    return HttpResponseRedirect(reverse('product:items_list'))

        return super(
            HomePageView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)

        sales = self.request.user.retailer_user.retailer.retailer_sales.all()
        sales_sum = sales.aggregate(
            total_sales=Sum('grand_total')
        )

        today_sales = (
            self.request.user.retailer_user.retailer.
            retailer_sales.filter(
                created_at__icontains=timezone.now().date()
            )
        )
        today_sales_sum = today_sales.aggregate(
            total_sales=Sum('grand_total')
        )

        context.update({
            'sales_count': sales.count(),
            'sales_sum': (
                int(sales_sum.get('total_sales')) if
                sales_sum.get('total_sales') else 0
            ),
            'today_sales_count': today_sales.count(),
            'today_sales_sum': (
                int(today_sales_sum.get('total_sales')) if
                today_sales_sum.get('total_sales') else 0
            )
        })

        return context


class CreateCustomer(FormView):
    form_class = CustomerForm
    template_name = 'customer/create_customer.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            CreateCustomer, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('customers'))
    
    def form_invalid(self, form):
        return super(CreateCustomer, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(
            CreateCustomer, self).get_context_data(**kwargs)

        customers = Customer.objects.filter(
            retailer=self.request.user.retailer_user.retailer.id)
        context.update({
            'customers': customers
        })
        return context


class CustomerTemplateView(TemplateView):
    template_name = 'customer/customer_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            CustomerTemplateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(
            CustomerTemplateView, self).get_context_data(**kwargs)

        customers = (
            self.request.user.retailer_user.retailer.
            retailer_customer.all().order_by('customer_name'))
        context.update({
            'customers': customers
        })
        return context


class CustomerUpdateView(UpdateView):
    form_class = CustomerForm
    template_name = 'customer/update_customer.html'
    model = Customer
    success_url = reverse_lazy('customers')

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            CustomerUpdateView, self).dispatch(request, *args, **kwargs)


class CreateFeedBack(FormView):
    form_class = FeedBackForm
    template_name = 'create_feedback.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            CreateFeedBack, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('create_feedback'))

    def form_invalid(self, form):
        return super(CreateFeedBack, self).form_invalid(form)

# class ReportsView(TemplateView):
#     template_name = 'reports.html'

#     def dispatch(self, request, *args, **kwargs):
#         # if not self.request.user.is_authenticated:
#         #     print('not authenticated')
#         #     return HttpResponseRedirect(reverse('login'))
#         # else:
#         #     print('authenticated')
#         #     if self.request.user.retailer_user:
#         #         if (
#         #             self.request.user.retailer_user.role_type ==
#         #                 self.request.user.retailer_user.ROLE_TYPE_SALESMAN
#         #         ):
#         #             return HttpResponseRedirect(reverse('sales:invoice_list'))
#         #     if self.request.user.retailer_user:
#         #         if (
#         #                 self.request.user.retailer_user.role_type ==
#         #                 self.request.user.retailer_user.ROLE_TYPE_DATA_ENTRY_USER
#         #         ):
#         #             return HttpResponseRedirect(reverse('product:items_list'))

#         return super(
#             ReportsView, self).dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         context = super(ReportsView, self).get_context_data(**kwargs)

#         sales = self.request.user.retailer_user.retailer.retailer_sales.all()
#         sales_sum = sales.aggregate(
#             total_sales=Sum('grand_total')
#         )

#         today_sales = (
#             self.request.user.retailer_user.retailer.
#             retailer_sales.filter(
#                 created_at__icontains=timezone.now().date()
#             )
#         )
#         today_sales_sum = today_sales.aggregate(
#             total_sales=Sum('grand_total')
#         )

#         context.update({
#             'sales_count': sales.count(),
#             'sales_sum': (
#                 int(sales_sum.get('total_sales')) if
#                 sales_sum.get('total_sales') else 0
#             ),
#             'today_sales_count': today_sales.count(),
#             'today_sales_sum': (
#                 int(today_sales_sum.get('total_sales')) if
#                 today_sales_sum.get('total_sales') else 0
#             )
#         })

#         return context
def sales_data(obj, stockout=None, date=None, week_date=None, month_date=None):
        # print('sales_data')
        sales = obj.aggregate(
            total_sales=Sum('grand_total')
        )

        data = {
            'sales': (
                int(sales.get('total_sales')) if
                sales.get('total_sales') else 0
            ),
        }

        profit = 0
        if stockout:
            try:
                selling_amount = stockout.aggregate(selling_amount=Sum('selling_price'))
                buying_amount = stockout.aggregate(buying_amount=Sum('buying_price'))
                selling_amount = selling_amount.get('selling_amount') or 0
                buying_amount = buying_amount.get('buying_amount') or 0
            except:
                selling_amount = 0
                buying_amount = 0

            profit = float(selling_amount) - float(buying_amount)
        data.update({
            'profit': profit
        })

        if week_date:
            data.update({
                'date': week_date.strftime('%a %d, %b')
            })
        elif month_date:
            data.update({
                'day': month_date.strftime('%b')
            })
        else:
            data.update({
                'date': date.strftime('%d-%b-%Y')
            })
        # print(data)
        return data
def daily(request):
    sales = []
    for day in range(12):
        sales_day = timezone.now() - relativedelta(days=day)
        retailer_sales = (
            request.user.retailer_user.retailer.
            retailer_sales.filter(created_at__icontains=sales_day.date())
        )

        retailer_products = (request.user.retailer_user.retailer.
                retailer_product.all().values_list('id', flat=True))

        stockout = StockOut.objects.filter(
            dated__icontains=sales_day.date(),
            product__in=retailer_products
        )

        data = sales_data(
            obj=retailer_sales, stockout=stockout, date=sales_day
        )
        sales.append(data)
    return sales

# def weekly(request):
#     sales = []
#     for week in range(1, 13):
#         sales_start_week = timezone.now() - relativedelta(weeks=week)
#         sales_end_week = timezone.now() - relativedelta(weeks=week - 1)

#         retailer_sales = (
#             request.user.retailer_user.retailer.retailer_sales.filter(
#                 created_at__gte=sales_start_week,
#                 created_at__lt=sales_end_week
#             )
#         )
#         retailer_products = (request.user.retailer_user.retailer.
#                                 retailer_product.all().values_list('id',
#                                                                 flat=True))

#         stockout = StockOut.objects.filter(
#             dated__gte=sales_start_week,
#             dated__lt=sales_end_week,
#             product__in=retailer_products
#         )
#         data = sales_data(
#             obj=retailer_sales, stockout=stockout, week_date=sales_end_week
#         )
#         sales.append(data)
#     return sales

def monthly(request):
    sales = []

    for month in range(12):
        date_month = timezone.now() - relativedelta(months=month)
        month_range = monthrange(
            date_month.year, date_month.month
        )
        start_month = datetime.datetime(
            date_month.year, date_month.month, 1)

        end_month = datetime.datetime(
            date_month.year, date_month.month, month_range[1]
        )

        retailer_sales = (
            request.user.retailer_user.retailer.retailer_sales.filter(
                created_at__gte=start_month,
                created_at__lt=end_month.replace(
                    hour=23, minute=59, second=59)
            )
        )

        retailer_products = (request.user.retailer_user.retailer.
                                retailer_product.all().values_list('id',
                                                                flat=True))
        stockout = StockOut.objects.filter(
            dated__gte=start_month,
            dated__lt=end_month.replace(
                    hour=23, minute=59, second=59),
            product__in=retailer_products
        )

        data = sales_data(
            obj=retailer_sales, stockout=stockout, month_date=end_month
        )
        sales.append(data)
    return sales

def reportView(request):
    if not request.user.is_authenticated:
        print('not authenticated')
        return HttpResponseRedirect(reverse('login'))
    else:
        
        daily_sales = daily(request)
        # weekly_sales = weekly(request)
        monthly_sales = monthly(request)
        # print(weekly_sales)
        
        return render(request, 'reports.html',
        {
            'daily_sales': daily_sales,
            # 'weekly_sales': weekly_sales,
            'monthly_sales': monthly_sales
        }
        )