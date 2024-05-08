import json
import uuid

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from app.forms import SearchForm
from app.models import Societe, History
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
    try:
        data = json.loads(request.GET.get('request')).get('record')
        societe = Societe.objects.get(uid=data['uid'])

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

        # Save export history
        history = History(
            societe=societe.name,  # Assuming societe has a 'name' field
            destinataire=recipient,
            copie=copie,
            target=data['target'],
            status=send['status'] == 'success',  # Convert status to boolean
            created_at=timezone.now(),
            message=data['message']
        )
        history.save()

        return JsonResponse(send, safe=False)
    except KeyError as e:
        return JsonResponse({'status': 'error', 'message': f'Missing key in request data: {e}'}, status=400)
    except ObjectDoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Societe not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An error occurred: {e}'}, status=500)


def get_history(request):
    records = {
        'status': 'error',
        'message': "Une erreur s'est produite"
    }
    try:
        history = History.objects.all().annotate(
            recid=F('uid')
        ).values('recid', 'societe', 'target', 'destinataire', 'copie', 'status', 'message', 'created_at')
        datas = [{key: value for key, value in data.items()} for data in history]
        records['status'] = 'success'
        records['message'] = 'Données générées avec succès !'
        records['total'] = len(datas)
        records['records'] = datas
    except Exception as e:
        write_log(str(e))

    return JsonResponse(records, safe=False)
