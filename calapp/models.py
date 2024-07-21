from django.db import models
from django.forms import ModelForm, DateInput, TextInput

# Create your models here.

class Appointment(models.Model):
    date = models.DateField("appointment date")
    description = models.CharField(max_length=256)
    yearly = models.BooleanField(default=False)
    owner = models.CharField(max_length=256)

    def __str__(self):
        if self.yearly:
            return "%d/%d (yearly): %s" % (self.date.day, self.date.month, self.description)
        else:
            return "%d/%d/%d: %s" % (self.date.day, self.date.month, self.date.year, self.description)


class AppointmentForm(ModelForm):
    class Meta:
        model = Appointment
        fields = '__all__'
        widgets = {
                'description': TextInput(attrs={'autofocus': True}),
                'date': DateInput(attrs={'type':'date'}),
                'owner': TextInput(attrs={'readonly': 'readonly'}),
                }


class Timer(models.Model):
    updated = models.DateTimeField("timer last updated")
    count = models.IntegerField(default=0)
    name = models.CharField(max_length=256)
    owner = models.CharField(max_length=256)
    running = models.BooleanField(default=False)


class Task(models.Model):
    owner = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    created = models.DateField('creation date')
    deadline = models.DateField('deadline')
    priority = models.IntegerField(default=0)
    done = models.BooleanField(default=False)
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, null=True, on_delete=models.CASCADE)

