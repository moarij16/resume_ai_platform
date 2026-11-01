from rest_framework import serializers


class OwnedResourceIdField(serializers.UUIDField):
    """
    UUID input field that only accepts the ID of a record the requesting user
    owns (see `UserOwnedModel.owned_by`). Another user's ID, a deleted record and
    a non-existent ID all get the same "not found" error, so callers can't probe
    for other users' data.

    Requires `request` in the serializer context. Returns the UUID unchanged.
    """

    def __init__(self, model, not_found_message="Not found.", **kwargs):
        self.model = model
        self.not_found_message = not_found_message
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not self.model.owned_by(user).filter(pk=value).exists():
            raise serializers.ValidationError(self.not_found_message)
        return value
