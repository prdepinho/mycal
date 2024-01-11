from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.http import Http404
from django.shortcuts import render
import datetime
import calendar

from .models import Appointment

# Create your views here.
def index(request):
    return HttpResponse("Hello world")


def month(request, month, year, forward):
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
        appointments = [[x, ""] for x in Appointment.objects.filter(date__range=[start, end]).order_by('date')]
        monthdays = [[x,y,""] for (x,y) in cal.itermonthdays2(year, month)]

        for appointment in appointments:
            if appointment[0].date <= datetime.date.today():
                appointment[1] = "passed"
                for mday in monthdays:
                    if mday[0] == appointment[0].date.day:
                        mday[2] = "passed"
                        break
            else:
                appointment[1] = "to come"
                for mday in monthdays:
                    if mday[0] == appointment[0].date.day:
                        mday[2] = "to come"
                        break

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

    return render(request, 'calapp/month.html', context={
            'scrollto': scrollto,
            'months': months,
        })
