from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import yaml


@api_view(['GET'])
@permission_classes([AllowAny])          # ← This fixes the AssertionError
def custom_schema_view(request, format=None):
    """
    Serve a fixed schema.yaml file.
    This is safe for multi-tenant setups because it doesn't run schema generation.
    """
    schema_path = settings.BASE_DIR / "schema.yaml"

    if not schema_path.exists():
        return JsonResponse({
            "error": f"schema.yaml not found. Expected location: {schema_path}",
            "tip": "Make sure the file is named exactly 'schema.yaml' next to manage.py"
        }, status=404)

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()

        # Support JSON format if requested
        if format == 'json' or request.query_params.get('format') == 'json':
            data = yaml.safe_load(yaml_content)
            return JsonResponse(data, safe=False)

        # Serve as YAML (recommended for Swagger UI + Redoc)
        response = HttpResponse(yaml_content, content_type='application/yaml; charset=utf-8')
        response['Content-Disposition'] = 'inline; filename="schema.yaml"'
        return response

    except Exception as e:
        return JsonResponse({
            "error": "Failed to read schema file",
            "detail": str(e)
        }, status=500)