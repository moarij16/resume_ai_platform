from django.urls import path, include

urlpatterns = [
    path("api/v1/users/", include("users.urls")),
    path("api/v1/resumes/", include("resumes.urls")),
    path("api/v1/jobs/", include("jobs.urls")),
    path("api/v1/documents/", include("generated_documents.urls")),
    path("api/v1/ats/", include("ats.urls")),
    path("api/v1/billing/", include("billing.urls")),
]
