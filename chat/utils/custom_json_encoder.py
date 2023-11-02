from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder


class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # Convert datetime object to a string representation
            return obj.isoformat()
        return super().default(obj)