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
    return render(request, 'home.html', {'form': form})


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
ckpt = os.environ['FEWREL_PATH'] + "/checkpoint/pair-bert-train_re3d_fewrel_format-train_re3d_fewrel_format-5-3-na3.pth.tar"
def do_analysis():
    """
        Runs the actual analysis in a different thread
    """
    global currently_analyzing
    try:
        print("starting analysis!")
        currently_analyzing = True
        d = DetectionFramework(ckpt_path=ckpt)
        d.clear_support_queries()
        d.load_support("temp/relation_support_dataset.csv", K=5)
        d.load_queries_predefined_head_tail_csv("temp/queries.csv")
        d.detect()
        currently_analyzing = False
    finally:
        currently_analyzing = False
    

def start_analysis(request):
    """
        Starts the analysis process
    """
    global currently_analyzing
    if request.method == "GET":

        if not currently_analyzing:
            t = Thread(target=do_analysis)
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
    global currently_analyzing