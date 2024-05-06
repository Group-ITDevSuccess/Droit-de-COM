import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
@login_required
def index(request):
    return render(request, 'app/index.html', {
        'path': request.path
    })


@login_required
@csrf_exempt
def load_data(request):
    data = json.loads(request.GET.get('request'))
    print(data.get('canevas'), data)
    return JsonResponse([], safe=False)
