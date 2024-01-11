from django.db import models

# Create your models here.

class Appointment(models.Model):
    date = models.DateField("appointment date")
    description = models.CharField(max_length=256)
    yearly = models.BooleanField(default=False)

    def __str__(self):
        if self.yearly:
            return "%d/%d (yearly): %s" % (self.date.day, self.date.month, self.description)
        else:
            return "%d/%d/%d: %s" % (self.date.day, self.date.month, self.date.year, self.description)
