from django.urls import path
from . import views

urlpatterns = [
    path('',views.upload_and_parse_resumes,name="resume_analyzer"),
    path('resume_results/',views.resume_results,name="resume_resultsurls"),
    path('clear/', views.clear_all_data, name='clear_all_data'),
    path('compose-email/', views.compose_email, name='compose_email'),
]
