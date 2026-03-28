from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import *

@api_view(['GET'])
def product(request):
    resp = {"products": Product.objects.all()}
    return Response(resp)