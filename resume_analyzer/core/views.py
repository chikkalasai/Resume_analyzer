from django.shortcuts import render,redirect
from django.http import HttpResponse

# Create your views here.
def hi(request):
    return render(request,'resume_upload.html')


import re
import spacy
import fitz  # PyMuPDF
from fuzzywuzzy import fuzz
from django.shortcuts import render
from .models import Resume, ParsedResume

nlp = spacy.load("en_core_web_sm")

# === Helper functions ===

def extract_text_from_pdf(file_path):
    text = ""
    pdf = fitz.open(file_path)
    for page in pdf:
        text += page.get_text()
    return text

def extract_emails(text):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)

def extract_names(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

def extract_phone(text):
    match = re.search(r'(\+?\d[\d\s-]{9,15})', text)
    return match.group(0) if match else ""

def check_name_in_email(name, email):
    score = fuzz.partial_ratio(name.lower(), email.lower())
    return score > 70, score

def match_names_with_emails(names, emails):
    for email in emails:
        for name in names:
            matched, score = check_name_in_email(name, email)
            if matched:
                return name, email
    return "", ""

def extract_skills(text, skill_list):
    text = text.lower()
    return [skill for skill in skill_list if skill.lower() in text]

def calculate_score(matched_skills, total_skills):
    if not total_skills:
        return 0.0
    score = (len(matched_skills) / len(total_skills)) * 10
    return round(min(score, 10), 2)

# === Main view ===

def upload_and_parse_resumes(request):
    if request.method == "POST":
        job_title = request.POST.get("job_title")
        required_skills = request.POST.get("required_skills", "")
        skill_list = [skill.strip() for skill in required_skills.split(",") if skill.strip()]
        files = request.FILES.getlist("resumes")
        count = 0

        for f in files:
            resume_obj = Resume.objects.create(file=f)
            text = extract_text_from_pdf(resume_obj.file.path)

            names = extract_names(text)
            emails = extract_emails(text)
            name, email = match_names_with_emails(names, emails)

            phone = extract_phone(text)
            matched_skills = extract_skills(text, skill_list)
            score = calculate_score(matched_skills, skill_list)
            print(name,email,phone,matched_skills)
            ParsedResume.objects.create(
                resume=resume_obj,
                name=name or "Unknown",
                email=email or "notfound@example.com",
                phone=phone or "NotExtracted",
                skills=", ".join(matched_skills),
                score=score
            )

            count += 1

        return redirect('resume_resultsurls')
    return render(request, "resume_upload.html")





from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.shortcuts import render
from .models import ParsedResume

def resume_results(request):
    min_score = request.GET.get("min_score", "")
    skill_query = request.GET.get("skill", "")

    resumes = ParsedResume.objects.all()

    if min_score:
        try:
            min_score_val = float(min_score)
            resumes = resumes.filter(score__gte=min_score_val)
        except ValueError:
            pass

    if skill_query:
        resumes = resumes.filter(skills__icontains=skill_query)

    # Sending emails on POST request
    if request.method == "POST":
        emails = [r.email for r in resumes if r.email]

        if emails:
            send_mail(
                subject="Congratulations! You are shortlisted",
                message="Dear Candidate,\n\nCongratulations! You have been shortlisted for further process.\n\nRegards,\nHR Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=False,
            )

            return render(request, "resume_results.html", {
                "resumes": resumes,
                "min_score": min_score,
                "skill_query": skill_query,
                "success": True,
            })

    return render(request, "resume_results.html", {
        "resumes": resumes,
        "min_score": min_score,
        "skill_query": skill_query,
    })


import os
import shutil
from django.contrib import messages
from .models import Resume, ParsedResume

# === View to Clear All Data ===
def clear_all_data(request):
    # 1. Delete all data from database
    Resume.objects.all().delete()
    ParsedResume.objects.all().delete()

    # 2. Delete uploaded resumes from 'media/resumes' folder
    resumes_folder = os.path.join(settings.MEDIA_ROOT, 'resumes')
    if os.path.exists(resumes_folder):
        shutil.rmtree(resumes_folder)
        os.makedirs(resumes_folder)  # recreate empty folder for future uploads

    # 3. Set success message
    messages.success(request, "✅ Successfully cleared all resumes and data!")

    # 4. Redirect to Upload Page
    return redirect('resume_analyzer')



#email
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from .models import ParsedResume

def compose_email(request):
    min_score = request.GET.get("min_score", "")
    skill_query = request.GET.get("skill", "")

    resumes = ParsedResume.objects.all()

    if min_score:
        try:
            resumes = resumes.filter(score__gte=float(min_score))
        except ValueError:
            pass

    if skill_query:
        resumes = resumes.filter(skills__icontains=skill_query)

    emails = [r.email for r in resumes if r.email]

    if request.method == "POST":
        subject = request.POST.get("subject", "")
        message = request.POST.get("message", "")

        if emails and subject and message:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=False,
            )
            return render(request, "compose_email.html", {
                "success": True,
                "emails": emails
            })

    return render(request, "compose_email.html", {
        "emails": emails
})