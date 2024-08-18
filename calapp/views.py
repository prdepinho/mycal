from django.shortcuts import render, redirect, HttpResponseRedirect
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader
from django.shortcuts import render
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.utils import timezone
import datetime
import calendar
import json
import math

from .models import Appointment, AppointmentForm, Timer, Task

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



# --- Timer ---

@login_required(login_url="/calapp/accounts/login")
def timer_page(request):
    id = int(request.GET.get('id', 0))
    page = int(request.GET.get('page', 0))
    obj_per_page = int(request.GET.get('obj_per_page', 10))

    if request.method == "GET":
        if id > 0:
            return _timer_detail(request, id)
        else:
            return render(request, "timer/timer_list.html", context={})
    else:
        return JsonResponse({}, status=405)


@login_required(login_url="/calapp/accounts/login")
def timer(request):
    id = int(request.GET.get('id', 0))
    page = int(request.GET.get('page', 0))
    obj_per_page = int(request.GET.get('obj_per_page', 10))

    if request.method == "GET":
        if id > 0:
            return _timer_get_by_id(request, id)
        else:
            return _timer_get_by_page(request, page, obj_per_page)

    elif request.method == "POST":
        return _timer_create(request)

    elif request.method == "PUT":
        return _timer_update(request)

    elif request.method == "DELETE":
        return _timer_delete(request, id)

    else:
        return JsonResponse({}, status=405)


def _timer_get_by_id(request, id):
    try:
        timer = Timer.objects.get(pk=id)
        return JsonResponse(model_to_dict(timer), status=200)
    except (EmptyPage, Timer.DoesNotExist):
        return JsonResponse({}, status=404)


def _timer_get_by_page(request, page, obj_per_page):
    try:
        timers = Timer.objects.filter(
                Q(owner=request.user.username)
                ).order_by('-updated')
        paginator = Paginator(timers, obj_per_page)
        page = paginator.page(page)
        objects = list(page.object_list.values())
        return JsonResponse({'objects': objects, 'has_next': page.has_next()}, status=200)
    except EmptyPage:
        return JsonResponse({}, status=404)


def _timer_detail(request, id):
    try:
        timer = Timer.objects.get(pk=id)
        return render(request, "timer/timer_detail.html", context={"timer": timer})
    except Timer.DoesNotExist:
        raise Http404("Timer not found")


def _timer_create(request):
    new_time = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())
    timer = Timer.objects.create(
            updated=new_time,
            count=0,
            name='New timer',
            owner=request.user.username)
    timer.save()
    return JsonResponse({"id": timer.id}, status=201)


def _timer_update(request):
    try:
        data = json.loads(request.body)
        timer = Timer.objects.get(pk=data['id'])

        started = not timer.running and data['running']
        new_time = timezone.make_aware(datetime.datetime.now(), timezone.get_current_timezone())

        if 'count' in data:
            timer.count = data['count']

        else:
            if not started:
                old_time = timer.updated
                delta = (new_time - old_time).total_seconds()
                timer.count += int(delta)
                logger.debug("old time: " + str(old_time))
                logger.debug("new time: " + str(new_time))
                logger.debug("dif: " + str(delta))

        timer.name = data['name']
        timer.running = data['running']
        timer.updated = new_time

        timer.save()
        return JsonResponse({}, status=204)
    except Timer.DoesNotExist:
        return JsonResponse(status=404)

def _timer_delete(request, id):
    timer = Timer.objects.get(pk=id)
    timer.delete()
    return JsonResponse({}, status=204)


# --- Tasks ---


@login_required(login_url="/calapp/accounts/login")
def tasks_list(request):
    tasks = Task.objects.filter(Q(owner=request.user.username)).order_by('done', 'priority').reverse()
    context = { 'tasks': tasks }
    return render(request, "tasks/tasks_list.html", context=context)


@login_required(login_url="/calapp/accounts/login")
def tasks_get_parents(request):
    if request.method == "GET":
        try:
            obj_per_page = int(request.GET.get("obj_per_page", 10))
            page = int(request.GET.get("page", 1))
            mode = request.GET.get("mode", "all")

            if mode == "all":
                tasks = Task.objects.filter(
                        Q(owner=request.user.username) & Q(parent=None)
                        ).order_by('done', '-priority')
            elif mode == "done":
                tasks = Task.objects.filter(
                        Q(owner=request.user.username) & Q(parent=None) & Q(done=True)
                        ).order_by('done', '-priority')
            elif mode == "active":
                tasks = Task.objects.filter(
                        Q(owner=request.user.username) & Q(parent=None) & Q(done=False)
                        ).order_by('done', '-priority')
            else:
                return JsonResponse({}, status=400)

            paginator = Paginator(tasks, obj_per_page)
            page = paginator.page(page)
            objects = list(page.object_list.values())

            return JsonResponse({"objects": objects, "has_next": page.has_next()}, status=200)
        except EmptyPage:
            JsonResponse({}, status=404);
    else:
        return JsonResponse({}, status=405)


@login_required(login_url="/calapp/accounts/login")
def tasks_get_children(request):
    if request.method == "GET":
        try:
            parent_id = request.GET.get("parent_id")
            if not parent_id:
                return JsonResponse({}, status=400)

            tasks = Task.objects.filter(
                    Q(owner=request.user.username) & Q(parent__id=parent_id)
                    ).order_by('-priority')
            objects = list(tasks.values())

            return JsonResponse({"objects": objects}, status=200)
        except EmptyPage:
            JsonResponse({}, status=404);
    else:
        return JsonResponse({}, status=405)


@login_required(login_url="/calapp/accounts/login")
def tasks_create(request):
    if request.method == "POST":
        task = Task.objects.create(
                owner=request.user.username,
                title="",
                created=datetime.date.today(),
                deadline=datetime.date.today(),
                priority=0,
                done=False,
                )
        task.save()
        return JsonResponse({"id": task.id}, status=200)
    else:
        return render(request, "tasks/tasks_detail.html", context={})


@login_required(login_url="/calapp/accounts/login")
def tasks_create_child(request):
    if request.method == "POST":
        data = json.loads(request.body)
        parent = Task.objects.get(pk=data['parent_id'])
        if not parent:
            return JsonResponse({}, status=404)
        task = Task.objects.create(
                owner=request.user.username,
                title="",
                created=datetime.date.today(),
                deadline=datetime.date.today(),
                priority=0,
                done=False,
                parent=parent,
                )
        task.save()
        return JsonResponse({"id": task.id}, status=200)
    return JsonResponse({}, status=400)


@login_required(login_url="/calapp/accounts/login")
def tasks_update(request):
    if request.method == "PUT":
        data = json.loads(request.body)
        task = Task.objects.get(pk=data['id'])

        if data['title']:
            task.title = data['title']
        if data['deadline']:
            task.deadline = datetime.datetime.strptime(data['deadline'], "%Y-%m-%d") if data['deadline'] != '' else task.deadline
        if data['priority']:
            task.priority = data['priority']
        if data['done'] is not None:
            task.done = data['done']
        if data['timer'] not in [None, 0]:
            task.timer = Timer.objects.get(id=data['timer'])
            task.timer.name = task.title
            task.timer.save()

        if task.parent is None:
            if task.done:
                apt_name = "(Done) %s" % (task.title)
            else:
                apt_name = "(%d) %s" % (task.priority, task.title)

            if not task.appointment:
                task.appointment = Appointment.objects.create(
                        owner=request.user.username,
                        date=task.deadline,
                        yearly=False,
                        description=apt_name,
                        )
                task.appointment.save()

            else:
                task.appointment.date = task.deadline
                task.appointment.description = apt_name
                task.appointment.save()

        task.save()
        return JsonResponse({}, status=200)
    return JsonResponse({}, status=405)


@login_required(login_url="/calapp/accounts/login")
def tasks_delete(request):
    if request.method == "DELETE":
        data = json.loads(request.body)
        task = Task.objects.get(pk=data['id'])
        if task.appointment:
            task.appointment.delete()
        task.delete()
        return JsonResponse({}, status=200)
    return JsonResponse({}, status=405)
