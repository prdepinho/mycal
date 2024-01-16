from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse
from django.template import loader
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
import datetime
import calendar

from .models import Appointment, AppointmentForm

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Create your views here.
def index(request):
    return HttpResponse("Hello world")


def logout_user(request):
    try:
        logout(request)
        return render(request, 'registration/logged_out.html', {})
    except Exception as e:
        return HttpResponse(str(e))

def register_user(request):
    try:
        if request.method == "POST":
            form = UserCreationForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('login')
        else:
            form = UserCreationForm()
        return render(request, 'registration/register.html', {'form': form})
    except Exception as e:
        return HttpResponse(str(e))



def _draw_months(request, year, month, forward):
    if month < 1 or month > 12:
        raise Http404("Month makes no sense: %s" % (month))

    cal = calendar.Calendar(6)

    months = {}
    start_month = month
    start_year = year

    for i in range(forward + 1):
        if i > 0:
            if month + 1 > 12:
                month = month + 1 - 12
                year = year + 1
            else:
                month = month + 1

        mid = year * 100 + month
        header = datetime.date(year, month, 1).strftime("%B, %Y")

        start = datetime.date(year, month, 1)
        end_month = month + 1 if month < 12 else 1
        end_year = year if end_month != 1 else year + 1
        end = datetime.date(end_year, end_month, 1)
        appointments = [[x, ""] for x in Appointment.objects.filter(owner=request.user.username).filter(date__range=[start, end]).order_by('date')]
        monthdays = [[x,y,"",None] for (x,y) in cal.itermonthdays2(year, month)]  # x is monthday, y is weekday

        for appointment in appointments:
            if appointment[0].date <= datetime.date.today():
                appointment[1] = "passed"
                for mday in monthdays:
                    if mday[0] == appointment[0].date.day:
                        mday[2] = "passed"
                        mday[3] = appointment[0]
                        break
            else:
                appointment[1] = "to come"
                for mday in monthdays:
                    if mday[0] == appointment[0].date.day:
                        mday[2] = "to come"
                        mday[3] = appointment[0]
                        break

        scrollto = None
        if month == datetime.date.today().month and year == datetime.date.today().year:
            scrollto = mid
            for appointment in appointments:
                if appointment[0].date.day == datetime.date.today().day:
                    appointment[1] = "today"
            for mday in monthdays:
                if mday[0] == datetime.date.today().day:
                    mday[2] = "today"
                    break

        months[mid] = {
            'header': header,
            'monthdays': monthdays,
            'appointments': appointments,
            }

    response = render(request, 'calapp/month.html', context={
            'scrollto': scrollto,
            'months': months,
        })
    return response


@login_required(login_url="/calapp/accounts/login")
def month(request, year, month, forward):
    response = _draw_months(request, year, month, forward)
    response.set_cookie('home_page', '/calapp/%d/%d/%d' % (year, month, forward))
    return response


@login_required(login_url="/calapp/accounts/login")
def default_month(request):
    today = datetime.date.today()
    response = _draw_months(request, today.year, today.month, forward=1)
    response.set_cookie('home_page', '/calapp')
    return response


@login_required(login_url="/calapp/accounts/login")
def show_year(request, year):
    response = _draw_months(request, year=year, month=1, forward=11)
    response.set_cookie('home_page', '/calapp/%d' % (year))
    return response


@login_required(login_url="/calapp/accounts/login")
def appointment(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            apt = form.save(commit=False)
            apt.owner = request.user.username
            apt.save()
            logger.debug(request.COOKIES.get('home_page', '/calapp'))
            return redirect(request.COOKIES.get('home_page', '/calapp'))
        else:
            return HttpResponse("Fail")
    else:
        form = AppointmentForm()
        return render(request, "calapp/appointment.html", context={"form": form})


@login_required(login_url="/calapp/accounts/login")
def appointment_day(request, year, month, day):
    try:
        form = AppointmentForm(initial={'owner': request.user.username, 'date': datetime.datetime(year, month, day)})
        if request.method == "POST":
            form = AppointmentForm(request.POST)
            if form.is_valid():
                apt = form.save(commit=False)
                apt.owner = request.user.username
                apt.save()
                return redirect(request.COOKIES.get('home_page', '/calapp'))

        return render(request, "calapp/appointment.html", context={"form": form})
    except Exception as e:
        return HttpResponse("error: %s" % str(e))



@login_required(login_url="/calapp/accounts/login")
def appointment_by_id(request, id):
    try:
        appointment = Appointment.objects.get(pk=id);
        if request.method == "POST":
            form = AppointmentForm(request.POST, instance=appointment)
            if form.is_valid():
                form.save()
                return redirect(request.COOKIES.get('home_page', '/calapp'))
            else:
                return HttpResponse("Fail")
        else:
            form = AppointmentForm(instance=appointment)
            return render(request, "calapp/appointment.html", context={"form": form})
    except Exception as e:
        return HttpResponse("error: %s" % str(e))





@login_required(login_url="/calapp/accounts/login")
def appointment_create(request):
    try:
        form = AppointmentForm(request.POST or None)
        if form.is_valid():
            apt = form.save(commit=False)
            apt.owner = request.user.username
            apt.save()
        context = {'form': form}
        return render(request, "calapp/appointment_create.html", context)
    except Exception as e:
        return HttpResponse("error: %s" % str(e))


@login_required(login_url="/calapp/accounts/login")
def appointment_detail(request, id):
    try:
        apt = Appointment.objects.get(pk=id)
        context = {'apt': apt}
        return render(request, "calapp/appointment_detail.html", context)
    except Exception as e:
        return HttpResponse("error: %s" % str(e))


@login_required(login_url="/calapp/accounts/login")
def appointment_update(request, id):
    try:
        apt = Appointment.objects.get(pk=id)
        form = AppointmentForm(request.POST or None, instance=apt)
        if form.is_valid():
            form.save()
            return redirect(request.COOKIES.get('home_page', '/calapp'))
        context = {'form': form, 'id':id}
        return render(request, "calapp/appointment_update.html", context)
    except Exception as e:
        return HttpResponse("error: %s" % str(e))


@login_required(login_url="/calapp/accounts/login")
def appointment_delete(request, id):
    try:
        apt = Appointment.objects.get(pk=id)
        if request.method == "POST":
            apt.delete()
            return redirect(request.COOKIES.get('home_page', '/calapp'))
        context = {}
        return render(request, 'calapp/appointment_delete.html', context)
    except Exception as e:
        return HttpResponse("error: %s" % str(e))



