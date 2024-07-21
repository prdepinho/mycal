from django.urls import path, include
from . import views

urlpatterns = [
        path('', views.default_month, name="default"),
        path('accounts/', include("django.contrib.auth.urls")),
        path('accounts/register', views.register_user, name="register_user"),
        path('accounts/logout', views.logout_user, name="logout"),

        path("select", views.select, name="select"),

        path('<int:year>', views.show_year, name="year"),
        path("<int:year>/<int:month>/<int:forward>", views.month, name="month"),
        path("appointment", views.appointment, name="appointment"),
        path("appointment/<int:id>", views.appointment_by_id, name="appointment_by_id"),
        path("appointment/<int:year>/<int:month>/<int:day>", views.appointment_day, name="appointment_day"),

        path("appointment_create", views.appointment_create, name="appointment_create"),
        path("appointment_detail/<int:id>", views.appointment_detail, name="appointment_detail"),
        path("appointment_update/<int:id>", views.appointment_update, name="appointment_update"),
        path("appointment_delete/<int:id>", views.appointment_delete, name="appointment_delete"),

        # --- 

        path("timer/", views.timer, name="timer"),
        path("timer/page/", views.timer_page, name="timer_page"),

        # ---
        path("tasks/", views.tasks_list, name="tasks_list"),
        path("tasks_get_parents", views.tasks_get_parents, name="tasks_parents"),
        path("tasks_get_children", views.tasks_get_children, name="tasks_children"),
        path("tasks_create", views.tasks_create, name="tasks_create"),
        path("tasks_create_child", views.tasks_create_child, name="tasks_create_child"),
        path("tasks_update", views.tasks_update, name="tasks_update"),
        path("tasks_delete", views.tasks_delete, name="tasks_delete"),

        ]
