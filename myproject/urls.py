"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from os import name

from django.contrib import admin
from django.urls import path
from my_app import views
from django.conf import settings
from django.conf.urls.static import static  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.home,name='home'),
    path('login/',views.user_login,name='login'),
    path('register',views.register,name='register'),
    path('logout/',views.user_logout,name='logout'),
    path('display-post/',views.display_post,name='display-post'),
    path('read-post/<int:id>/', views.read_post, name='read-post'),
    path('add-post/',views.add_post,name='add-post'),
    path('update-post/<int:id>/', views.update_post, name='update-post'),
    path('delete-post/<int:id>/', views.delete_post, name='delete-post'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
