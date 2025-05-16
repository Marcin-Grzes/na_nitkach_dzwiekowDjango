"""
URL configuration for webService project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from events import views
from events.views import (HomeView, Base, TestCalendar, ReservationSuccessView, ReservationAvailabilityView,
                          UniversalReservationView, EventsDataApiView)

# from events.views import ReservationsView
# from events.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='index'),
    path('base/', Base.as_view(), name='base'),
    path('test/', TestCalendar.as_view(), name='test'),
    path('events/<int:event_id>/reservation/<int:reservation_id>/success/', ReservationSuccessView.as_view(),
         name='reservation_success'),
    # path('rezerwation', ReservationsView.as_view(), name='rezerwation'),
    path('calendar/', views.CalendarView.as_view(), name='event_calendar'),
    path('<int:event_id>/', views.EventDetailView.as_view(), name='event_detail'),
    path('type/<slug:type_slug>/', views.EventsByTypeView.as_view(), name='events_by_type'),
    path('tinymce/', include('tinymce.urls')),
    path('events/<int:event_id>/reservation/', views.EventReservationView.as_view(), name='event_reservation'),
    path('reservation/cancel/<uuid:token>/', views.CancelReservationView.as_view(), name='cancel_reservation'),
    path('api/calendar-events/', views.CalendarEventsApiView.as_view(), name='calendar_events_api'),
    path('api/events/<int:event_id>/check-reservation/', ReservationAvailabilityView.as_view(), name='check_reservation_availability'),
    path('reservation/', views.UniversalReservationView.as_view(), name='reservation'),
    path('api/events-data/', views.EventsDataApiView.as_view(), name='events_data_api'),
]
# Tylko w wersji developerskiej
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

