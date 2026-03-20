from rest_framework.exceptions import APIException


class AIGenerationFailed(APIException):
    status_code = 503
    default_detail = "AI generation failed. Please try again."
    default_code = "ai_generation_failed"


class AIProviderNotConfigured(APIException):
    status_code = 500
    default_detail = "AI provider is not configured."
    default_code = "ai_provider_not_configured"
