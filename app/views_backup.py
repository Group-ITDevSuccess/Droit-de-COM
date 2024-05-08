import json
import uuid

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from app.forms import SearchForm
from app.models import Societe
from data import fetch_data_from_database
from utils import write_log


# Create your views here.
@login_required
def index(request):
    form = SearchForm()
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            societe = form.cleaned_data['societe']
            target = form.cleaned_data['target']
            return redirect('app:reverse_index', uid=societe, target=target)
    return render(request, 'app/index.html', {
        'path': request.path,
        'form': form
    })


@login_required
def reverse_index(request, uid, target):
    societe = uid
    form = SearchForm(initial={'societe': societe, 'target': target})
    return render(request, 'app/index.html', {
        'path': request.path,
        'form': form,
        'uid': uid,
        'target': target
    })


@login_required
@csrf_exempt
def load_data(request):
    data = request.POST

    uid = data.get('uid')
    target = data.get('target')
    records = {
        'status': 'error'
    }
    if uid != '' and target != '':
        canevas = data.get('canevas')
        try:
            societe = Societe.objects.get(uid=uid)
            records = fetch_data_from_database(
                canevas=canevas,
                target=target,
                types=societe.type,
                societe=societe
            )
        except Societe.DoesNotExist:
            print("Societe Inexistant !")
            records['message'] = "Societe Inexistant !"
        except Exception as e:
            write_log(str(e))
            records['message'] = "Une erreur c'est produit !"
        print(records)
    return JsonResponse(records, safe=False)


@login_required
@csrf_exempt
def export_data(request):
    print(request)
    print(request.GET)
    print(request.body)
    print(request.POST)
    pq_filename = request.GET.get('pq_filename')
    print(pq_filename)
    return JsonResponse({'filename': 'filename.json'}, safe=False)
