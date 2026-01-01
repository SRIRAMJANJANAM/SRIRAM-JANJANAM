"""
URL configuration for profileproject project.

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
from testapp import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home_view),
    path('contact/',views.contact_view),
    path('skills/',views.skill_view),
    path('thanks/',views.thank_view),
    path('about/',views.about_view),
    path('chat/', views.chat_view, name='chat'),
    path('experiences/', views.experience_view, name='experiences'),

    path('chat/clear/', views.chat_clear_session, name='chat_clear'),
    path('chat/status/', views.chat_status, name='chat_status'),
    
    path('api/experiences/', views.experience_list_api, name='experience-list'),
    path('api/experiences/<int:experience_id>/', views.experience_detail_api, name='experience-detail'),
    path('api/experiences/bulk/', views.experience_bulk_api, name='experience-bulk'),
    path('api/experiences/search/', views.experience_search_api, name='experience-search'),
    path('api/experiences/stats/', views.experience_stats_api, name='experience-stats'),
    path('api/experiences/export/', views.experience_export_api, name='experience-export'),
]
