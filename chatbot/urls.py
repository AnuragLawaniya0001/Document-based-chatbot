from django.urls import path
from .views import home, upload_file, chat

urlpatterns = [
    path('', home, name='home'),
    path('upload/', upload_file, name='upload_file'),
    path('chat/', chat, name='chat'),
]
