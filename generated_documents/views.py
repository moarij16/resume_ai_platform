from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GeneratedDocument
from .serializers import (
    CoverLetterInputSerializer,
    GeneratedDocumentSerializer,
    LinkedInBioInputSerializer,
    ResumeGenerateSerializer,
    ResumeRefactorInputSerializer,
)
from .services.generator import (
    generate_cover_letter,
    generate_linkedin_bio,
    generate_resume,
    generate_resume_refactor,
)


class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]
    serializer_class = GeneratedDocumentSerializer

    def get_queryset(self):
        return GeneratedDocument.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        document = self.get_object()
        # Use "file_format" to avoid collision with DRF's built-in ?format= content-negotiation param
        fmt = request.query_params.get("file_format", "pdf").lower()
        stem = f"{document.document_type}_{document.id}"

        if fmt == "pdf":
            if document.document_type not in _RESUME_TYPES:
                return Response(
                    {
                        "error": "PDF download is only available for resume and resume_refactor documents."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            payload = render_pdf(document)
            response = HttpResponse(payload, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{stem}.pdf"'
            return response

        if fmt == "docx":
            if document.document_type not in _RESUME_TYPES:
                return Response(
                    {
                        "error": "DOCX download is only available for resume and resume_refactor documents."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            payload = render_docx(document)
            response = HttpResponse(
                document.document_content,
                content_type="text/plain",
            )
            filename = f"{document.document_type}_{document.id}.txt"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        # TODO: implement pdf / docx once reportlab / python-docx is added
        return Response(
            {"error": f"Format '{fmt}' is not yet supported. Use format=txt."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["post"], url_path="cover-letter")
    def cover_letter(self, request):
        serializer = CoverLetterInputSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        document = generate_cover_letter(
            user=request.user,
            resume_id=serializer.validated_data["resume_id"],
            job_id=serializer.validated_data.get("job_id"),
        )
        return Response(
            GeneratedDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="linkedin")
    def linkedin(self, request):
        serializer = LinkedInBioInputSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        document = generate_linkedin_bio(
            user=request.user,
            resume_id=serializer.validated_data["resume_id"],
        )
        return Response(
            GeneratedDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="refactor")
    def refactor(self, request):
        serializer = ResumeRefactorInputSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        document = generate_resume_refactor(
            user=request.user,
            resume_id=serializer.validated_data["resume_id"],
            job_id=serializer.validated_data.get("job_id"),
        )
        return Response(
            GeneratedDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        serializer = ResumeGenerateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        document = generate_resume(
            user=request.user,
            resume_id=serializer.validated_data["resume_id"],
            job_id=serializer.validated_data.get("job_id"),
        )
        return Response(
            GeneratedDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )
