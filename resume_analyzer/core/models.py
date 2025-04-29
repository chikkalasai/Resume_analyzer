from django.db import models

# Create your models here.
from django.db import models

class Resume(models.Model):
    file = models.FileField(upload_to='resumes/')
    uploaded_on = models.DateTimeField(auto_now_add=True)

class ParsedResume(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    skills = models.TextField()
    score = models.FloatField()
    extracted_on = models.DateTimeField(auto_now_add=True)