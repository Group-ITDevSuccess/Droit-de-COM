import json
import uuid

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from app.forms import SearchForm
from app.models import Societe
from data import fetch_data_from_database, export_data_in_config, custom_send_email
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
        'societe': Societe.objects.get(uid=uid).name,
        'target': target
    })


@login_required
@csrf_exempt
def load_data(request):
    records = {
        'status': "error"
    }

    try:
        data = json.loads(request.GET.get('request'))
        uid = data.get('uid')
        target = data.get('target')

        if uid != '' and target != '':
            canevas = data.get('canevas')
            societe = Societe.objects.get(uid=uid)
            records = fetch_data_from_database(
                canevas=canevas,
                target=target,
                types=societe.type,
                societe=societe,
            )
        records['status'] = "success"

    except Societe.DoesNotExist:
        print("Societe Inexistant !")
        records['message'] = "Societe Inexistant !"

    except Exception as e:
        write_log(f"Erreur : {str(e)}")
        records['message'] = "Une erreur c'est produit !"
    return JsonResponse(records, safe=False)


@login_required
@csrf_exempt
def export_data(request):
    data = json.loads(request.GET.get('request')).get('record')
    societe = Societe.objects.get(uid=data['uid'])
    print(data)
    file = export_data_in_config(societe=societe, champs=data['champs'], target=data['target'])
    recipient = str(data['destinataire']).replace(';', ',')
    copie = str(data['copie']).replace(';', ',')
    send = custom_send_email(
        target=data['target'],
        recipient_email=recipient,
        copie_email=copie,
        attachment_filename=file,
        message_text=data['message']
    )
    return JsonResponse(send, safe=False)
