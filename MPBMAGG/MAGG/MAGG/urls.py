"""
URL configuration for MAGG project.

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
from django.urls import path
from memeApp import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("start_scraping/", views.start_scraping, name="start_scraping"),
    path("get_results/", views.get_results, name="get_results"),
    path('admin/', admin.site.urls),
    path('', views.index),
    path('Analysis', views.Analysis),
    path('Owntest', views.own_test),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)