from django.urls import path
from .views import *

app_name = 'decision_bot'

urlpatterns = [
    path('analyze_translation', analyze_translation, name='analyze_translation'),
]