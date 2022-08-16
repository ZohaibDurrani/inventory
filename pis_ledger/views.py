# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from http.client import HTTPResponse
from struct import pack
from django.views.generic import FormView, TemplateView
from django.http import HttpResponseRedirect
from django.db.models import Sum
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render, redirect
from pis_com.models import Customer
from pis_com.forms import CustomerForm
from pis_ledger.forms import LedgerForm
from  pis_ledger.forms import Ledger
from pis_com.models import Customer


class AddNewLedger(FormView):
    form_class = CustomerForm
    template_name = 'ledger/create_ledger.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))

        return super(AddNewLedger, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        customer = form.save()
        ledger_form_kwargs = {
            'retailer': self.request.POST.get('retailer'),
            'customer': customer.id,
            'person':self.request.POST.get('customer_type'),
            'amount': self.request.POST.get('amount'),
            'payment_amount': self.request.POST.get('payment_amount'),
            'payment_type': self.request.POST.get('payment_type'),
            'description': self.request.POST.get('description'),
        }

        ledger_form = LedgerForm(ledger_form_kwargs)
        if ledger_form.is_valid():
            ledger_form.save()

        return HttpResponseRedirect(reverse('ledger:customer_ledger_list'))

    def form_invalid(self, form):
        return super(AddNewLedger, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(AddNewLedger, self).get_context_data(**kwargs)
        customers = Customer.objects.filter(
            retailer=self.request.user.retailer_user.retailer)

        context.update({
            'customers': customers
        })

        return context


class AddLedger(FormView):
    template_name = 'ledger/add_customer_ledger.html'
    form_class = LedgerForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(AddLedger, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        print(self.request.POST.get('dated'))
        print('+++++++++++++++++++++++++++++++++')
        print('+++++++++++++++++++++++++++++++++')
        print('+++++++++++++++++++++++++++++++++')
        ledger = form.save()
        return HttpResponseRedirect(
            reverse('ledger:customer_ledger_detail', kwargs={
                'customer_id': self.kwargs.get('customer_id')
            })
        )

    def form_invalid(self, form):
        return super(AddLedger, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(AddLedger, self).get_context_data(**kwargs)
        try:
            customer = (
                self.request.user.retailer_user.retailer.
                retailer_customer.get(id=self.kwargs.get('customer_id'))
            )
        except ObjectDoesNotExist:
            raise Http404('Customer not found with concerned User')

        context.update({
            'customer': customer
        })
        return context


class CustomerLedgerView(TemplateView):
    template_name = 'ledger/customer_ledger_list.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            CustomerLedgerView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CustomerLedgerView, self).get_context_data(**kwargs)
        customers = (
            self.request.user.retailer_user.retailer.
            retailer_customer.all().order_by('customer_name')
        ).order_by('customer_name')
        customer_ledger = []

        for customer in customers:
            customer_data = {}
            ledger = customer.customer_ledger.all().aggregate(Sum('amount'))
            payment_ledger = (
                customer.customer_ledger.all()
                .aggregate(Sum('payment'))
            )
            if payment_ledger.get('payment__sum'):
                payment_amount = float(payment_ledger.get('payment__sum'))
            else:
                payment_amount = 0

            if ledger.get('amount__sum'):
                ledger_amount = float(ledger.get('amount__sum'))
            else:
                ledger_amount = 0

            # remaining_ledger = '%g' % (
            #         ledger_amount - payment_amount
            # )
            print('_________________________')
            print('Summition',Ledger.objects.all().aggregate(Sum('amount')))
            print('Adaigi', Ledger.objects.all().aggregate(Sum('payment')))
            print('____________________________')
            sum_of_total_amount = Ledger.objects.all().aggregate(Sum('amount'))
            sum_of_total_payment = Ledger.objects.all().aggregate(Sum('payment'))
            print('__________')
            print(float(sum_of_total_amount.get('amount__sum') or 0))
            print(float(sum_of_total_payment.get('payment__sum') or 0))
            sum_of_total_amount = float(sum_of_total_amount.get('amount__sum') or 0)
            sum_of_total_payment = float(sum_of_total_payment.get('payment__sum') or 0)
            print('__________')
            remaining_ledger = ledger_amount - payment_amount

            print('Test Remaining', ledger_amount-payment_amount)
            print('Remaining Ledger',remaining_ledger)
            

            customer_data.update({
                'id': customer.id,
                'ledger_amount': ledger_amount,
                'payment_amount': payment_amount,
                'customer_name': customer.customer_name,
                'customer_phone': customer.customer_phone,
                'remaining_ledger': remaining_ledger,
                'customer_type':customer.customer_type,
            })

            customer_ledger.append(customer_data)

        ledgers = Ledger.objects.all()
        if ledgers:
            grand_ledger = ledgers.aggregate(Sum('amount'))
            print(grand_ledger, '1')
            grand_ledger = float(grand_ledger.get('amount__sum') or 0)
            print(grand_ledger, '2')
            grand_payment = ledgers.aggregate(Sum('payment'))
            print('grand_payment', grand_payment)
            grand_payment = float(grand_payment.get('payment__sum') or 0)
            print('grand_payment sum', grand_payment)


            total_remaining_amount = grand_ledger - grand_payment
            print('Total Remaining', total_remaining_amount)
        else:
            total_remaining_amount = 0

        context.update({
            'customer_ledgers': customer_ledger,
            'total_remaining_amount': total_remaining_amount,
            'sum_total_amount': sum_of_total_payment,
            'sum_total_payment': sum_of_total_amount,
        })
        # print(context)
        return context


class CustomerLedgerDetailsView(TemplateView):
    template_name = 'ledger/customer_ledger_details.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(
            CustomerLedgerDetailsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(
            CustomerLedgerDetailsView, self).get_context_data(**kwargs)

        try:
            customer = Customer.objects.get(
                id=self.kwargs.get('customer_id')
            )
        except Customer.DoesNotExist:
            raise Http404

        ledgers = customer.customer_ledger.all()
        if ledgers:
            ledger_total = ledgers.aggregate(Sum('amount'))
            ledger_total = float(ledger_total.get('amount__sum'))
            sum_ledger_amount = ledger_total
            print('Total Leger Amount', sum_ledger_amount)
            context.update({

            })
        else:
            ledger_total = 0

        if ledgers:
            payment_total = ledgers.aggregate(Sum('payment'))
            payment_total = float(payment_total.get('payment__sum'))
            sum_of_payment = payment_total
            print('Total Payment Amount',sum_of_payment)
            context.update({

            })
        else:
            payment_total = 0
        
        print('Test_Remaining', ledger_total - payment_total)
        context.update({
            'customer': customer,
            'ledgers': ledgers.order_by('-dated'),
            'ledger_total': '%g' % ledger_total,
            'payment_total': '%g' % payment_total,
            # 'remaining_amount': '%g' % (ledger_total - payment_total)
            'remaining_amount': (ledger_total - payment_total),
            'sum_of_legder': sum_ledger_amount,
            'sum_of_payment': sum_of_payment,
        })

        return context


class AddPayment(FormView):
    template_name = 'ledger/add_payment.html'
    form_class = LedgerForm

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        return super(AddPayment, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ledger = form.save()
        return HttpResponseRedirect(
            reverse('ledger:customer_ledger_detail', kwargs={
                'customer_id': self.kwargs.get('customer_id')
            })
        )

    def form_invalid(self, form):
        return super(AddPayment, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(AddPayment, self).get_context_data(**kwargs)
        try:
            customer = (
                self.request.user.retailer_user.retailer.
                retailer_customer.get(id=self.kwargs.get('customer_id'))
            )
        except ObjectDoesNotExist:
            raise Http404('Customer not found with concerned User')

        context.update({
            'customer': customer
        })
        return context


def updateLedgers(request):
    if request.method=="GET":
        id=request.GET.get('id')
        # print("asdkfjasdjkf",id)
        ledgers=Ledger.objects.filter(customer__id=id).get()
        return render(request, 'ledger/updateLedgers.html', {'ledgers': ledgers})
    elif request.method=="POST":
        id=request.POST.get('ledgers_id')
        amount=request.POST.get('amount')
        Ledger.objects.filter(id=id).update(amount=amount)
        return HttpResponseRedirect(reverse("ledger:customer_ledger_list"))

def deletecustomerledger(request):
    if request.method=="GET":
        id=request.GET.get('id')
        # print("asdkfjasdjkf",id)
        Ledger.objects.filter(customer__id=id).delete()
        Customer.objects.filter(id=id).delete()
        # ledgers.delete()
        # print("asdkfjasdjkf",ledgers)
        return HttpResponseRedirect(reverse("ledger:customer_ledger_list"))

def deleteledgerdetails(request):
    if request.method=="GET":
        id=request.GET.get('id')
        # print("asdkfjasdjkf",id)
        Ledger.objects.filter(id=id).delete()
        return HttpResponseRedirect(reverse("ledger:customer_ledger_list"))