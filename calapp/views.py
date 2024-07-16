from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import HttpResponse
from django.template import loader
from django.http import Http404
from django.shortcuts import render
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import datetime
import calendar

from .models import Appointment, AppointmentForm, Timer

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


@login_required(login_url="/calapp/accounts/login")
def select(request):
    try:
        return render(request, 'calapp/select.html', {})
    except Exception as e:
        return HttpResponse(str(e))


def _draw_months(request, year, month, forward):
    if month < 1 or month > 12:
        raise Http404("Month makes no sense: %s" % (month))

    cal = calendar.Calendar(6)

    months = {}
    start_month = month
    start_year = year
    today = datetime.date.today()

    logger.debug(request.COOKIES.get('last_visited_month', ''))
    scrollto = request.COOKIES.get('last_visited_month', '')

    for i in range(forward + 1):
        if i > 0:
            if month + 1 > 12:
                month = month + 1 - 12
                year = year + 1
            else:
                month = month + 1

        # for each month
        mid = year * 100 + month
        header = datetime.date(year, month, 1).strftime("%B, %Y")

        start = datetime.date(year, month, 1)  # start of the current month
        _, end_day = calendar.monthrange(year, month)
        end = datetime.date(year, month, end_day)  # end of month
        appointments = [[x, ""] for x in Appointment.objects.filter(
            Q(owner=request.user.username)
            & ( 
                Q(date__range=[start, end]) 
                | (
                    Q(yearly=True) & Q(date__month=month)
                )
            )
        ).order_by('date__day')]

        monthdays = [[x,y,"",None] for (x,y) in cal.itermonthdays2(year, month)]  # x is monthday, y is weekday

        for appointment in appointments:
            if appointment[0].yearly:
                appointment[0].date = datetime.date(year, appointment[0].date.month, appointment[0].date.day)

            if appointment[0].date <= today:
                appointment[1] = "passed yearly" if appointment[0].yearly else "passed"
                for mday in monthdays:
                    if mday[0] == appointment[0].date.day:
                        if mday[2] != "passed":
                            mday[2] = "passed yearly" if appointment[0].yearly else "passed"
                            mday[3] = appointment[0]
                        break
            else:
                appointment[1] = "to come yearly" if appointment[0].yearly else "to come"
                for mday in monthdays:
                    if mday[0] == appointment[0].date.day:
                        if mday[2] != "to come":
                            mday[2] = "to come yearly" if appointment[0].yearly else "to come"
                            mday[3] = appointment[0]
                        break

        if month == today.month and year == today.year:
            scrollto = mid if scrollto == '' else scrollto
            for appointment in appointments:
                if appointment[0].date.day == today.day:
                    appointment[1] = "today"
            for mday in monthdays:
                if mday[0] == today.day:
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

        response = render(request, "calapp/appointment.html", context={"form": form})
        return response
    except Exception as e:
        return HttpResponse("error: %s" % str(e))



@login_required(login_url="/calapp/accounts/login")
def appointment_by_id(request, id):
    try:
        apt = Appointment.objects.get(pk=id);
        if request.method == "POST":
            form = AppointmentForm(request.POST, instance=apt)
            if form.is_valid():
                form.save()
                return redirect(request.COOKIES.get('home_page', '/calapp'))
            else:
                return HttpResponse("Fail")
        else:
            form = AppointmentForm(instance=apt)
            response = render(request, "calapp/appointment.html", context={"form": form})
            return response
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
        response = render(request, "calapp/appointment_create.html", context)
        return response
    except Exception as e:
        return HttpResponse("error: %s" % str(e))


@login_required(login_url="/calapp/accounts/login")
def appointment_detail(request, id):
    try:
        apt = Appointment.objects.get(pk=id)
        context = {'apt': apt}
        response = render(request, "calapp/appointment_detail.html", context)
        return response
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
        response = render(request, "calapp/appointment_update.html", context)
        return response
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
        response = render(request, 'calapp/appointment_delete.html', context)
        return response
    except Exception as e:
        return HttpResponse("error: %s" % str(e))


# ---

@login_required(login_url="/calapp/accounts/login")
def timer_list(request):
    timers = Timer.objects.filter(Q(owner=request.user.username)).order_by('updated')
    context = { 'timers': timers }
    return render(request, "timer/timer_list.html", context=context)

@login_required(login_url="/calapp/accounts/login")
def timer_detail(request, id):
    timer = Timer.objects.get(pk=id)
    context = { 'timer': timer }
    return render(request, "timer/timer_detail.html", context=context)

@login_required(login_url="/calapp/accounts/login")
def timer_create(request):
    timer = Timer.objects.create(updated=datetime.date.today(), count=0, name='New timer',
            owner=request.user.username)
    timer.save()
    return redirect('/calapp/timer')

@login_required(login_url="/calapp/accounts/login")
def timer_delete(request, id):
    timer = Timer.objects.get(pk=id)
    timer.delete()
    return redirect('/calapp/timer')

@login_required(login_url="/calapp/accounts/login")
def timer_update(request, id, name, count):
    timer = Timer.objects.get(pk=id)
    timer.name = name
    timer.count = count
    timer.updated = datetime.date.today()
    timer.save()
    return redirect('/calapp/timer/' + str(id))

