from rest_framework.exceptions import APIException

# Messages here are shown to end users. Never put provider error text in them;
# log the underlying error server-side instead (see generated_documents/services/utils.py).


class AIGenerationFailed(APIException):
    status_code = 503
    default_detail = "AI generation failed. Please try again."
    default_code = "ai_generation_failed"


class AIProviderNotConfigured(APIException):
    status_code = 503
    default_detail = "AI features are not available right now. Please try again later."
    default_code = "ai_unavailable"


class AIRateLimited(APIException):
    status_code = 503
    default_detail = "The AI service is busy right now. Please wait a minute and try again."
    default_code = "ai_rate_limited"
