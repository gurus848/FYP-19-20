from django.http import HttpResponse
from django.shortcuts import render
from .forms import RelExInfoForm
import json
from django.views.decorators.cache import never_cache
import os
import sys
sys.path.insert(0, os.environ['FEWREL_PATH'])
from fyp_detection_framework import DetectionFramework
from threading import Thread

@never_cache
def home(request):
    """
        Renders the home page of the app.
    """
    form = RelExInfoForm()
    data = []
    for i in results:
        data.append({'sentence':i[0], 'head':i[1], 'tail':i[2], 'pred_relation':i[3]})
    ckpts = [f for f in os.listdir(os.environ['FEWREL_PATH'] + "/checkpoint") if '.pth.tar' in f]
    return render(request, 'home.html', {'form': form, 'data': data, 'ckpts':ckpts})


def handle_uploaded_file(f, fname):
    """
        Takes the uploaded files and saves them appropriately to disk.
    """
    with open(fname, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def rel_ex_files(request):
    """
        Uploads the selected relation support dataset and queries dataset from the user.
    """
    global results
    if request.method == "POST":
        relation_support_dataset = request.FILES['relation_support_dataset']
        queries_dataset = request.FILES['queries_dataset']
        handle_uploaded_file(relation_support_dataset, 'temp/relation_support_dataset.csv')
        handle_uploaded_file(queries_dataset, 'temp/queries.csv')
        results = []

        return HttpResponse(
            json.dumps({'success':'success'}),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"error": "error, GET request not supported"}),
            content_type="application/json"
        )


currently_analyzing = False
results = []
cancel_flag=[False]
def do_analysis(ckpt):
    """
        Runs the actual analysis in a different thread
    """
    global currently_analyzing, results
    try:
        print("starting analysis!")
        currently_analyzing = True
        results = []
        ckpt = os.environ['FEWREL_PATH'] + "/checkpoint/" + ckpt
        d = DetectionFramework(ckpt_path=ckpt)
        d.clear_support_queries()
        d.load_support("temp/relation_support_dataset.csv", K=5)
        d.load_queries_predefined_head_tail_csv("temp/queries.csv")    #TODO: generalize it to allow for non-predefined head and tail also
        d.detect(rt_results=results, cancel_flag=cancel_flag)
        currently_analyzing = False
    except ValueError as e:
        # TODO: handle the cases where there's an issue with the input data
        pass
    finally:
        currently_analyzing = False
    

def start_analysis(request):
    """
        Starts the analysis process
    """
    if request.method == "GET":

        if not currently_analyzing:
            cancel_flag[0] = False
            t = Thread(target=do_analysis, args=(request.GET.get('ckpt', 'pair-bert-train_re3d_fewrel_format-train_re3d_fewrel_format-5-3-na3.pth.tar'),))
            t.start()
            return HttpResponse(
                json.dumps({"success": "analysis started"}),
                content_type="application/json"
            )
        else:
            return HttpResponse(
                json.dumps({"error": "error, analysis already running"}),
                content_type="application/json"
            )
    else:
        return HttpResponse(
            json.dumps({"error": "error, POST request not supported"}),
            content_type="application/json"
        )
        
        

def get_analysis_results(request):
    """
        Returns the periodic analysis results as a specific json list
    """
    if not currently_analyzing and len(results) == 0:
        return HttpResponse(
            json.dumps({'status':'analysis_not_running'}),
            content_type="application/json"
        )
    else:
        client_index_till = int(request.GET.get('cur_index_reached', 0))
        new_data = []
        for i in results[client_index_till:]:
            new_data.append({'sentence':i[0], 'head':i[1], 'tail':i[2], 'pred_relation':i[3]})
        status = 'analysis_in_progress'
        if not currently_analyzing:
            status = 'finished_analysis'
        return HttpResponse(
            json.dumps({'status':status, 'new_data':new_data}),
            content_type="application/json"
        )
    
def cancel_analysis(request):
    """
        Cancels the analysis if it is currently running.
    """
    cancel_flag[0] = True
    if not currently_analyzing:
        return HttpResponse(
            json.dumps({'error':"error"}),
            content_type="application/json"
        )
    else:
        return HttpResponse(
            json.dumps({'success':"success"}),
            content_type="application/json"
        )