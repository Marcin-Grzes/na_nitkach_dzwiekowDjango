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
from events.views import HomeView

# from events.views import RezerwationsView
# from events.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    # path('rezerwation', RezerwationsView.as_view(), name='rezerwation'),
    path('', views.EventListView.as_view(), name='event_list'),
    path('<int:event_id>/', views.EventDetailView.as_view(), name='event_detail'),
    path('type/<slug:type_slug>/', views.EventsByTypeView.as_view(), name='events_by_type'),
    path('tinymce/', include('tinymce.urls')),
    path('events/<int:event_id>/reservation/', views.EventReservationView.as_view(), name='event_reservation'),
    path('reservation/cancel/<uuid:token>/', views.CancelReservationView.as_view(), name='cancel_reservation'),
]
# Tylko w wersji developerskiej
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)