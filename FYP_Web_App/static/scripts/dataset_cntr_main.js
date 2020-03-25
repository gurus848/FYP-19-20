// using jQuery - to ensure that the csrf token is set when a form is submitted
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue =   decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// to make form submits work - need to pass the CSRF token
var csrftoken = getCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


//called when the webpage has been fully loaded.
$(document).ready(function() {
    $("#dataset_cntr_nav").addClass("active");
    set_num_rels_exs(5, 3);
});

$('#upload_csv_form').on('submit', function(event){
    event.preventDefault();
    var formData = new FormData();
    var csv_file_name = $('#id_existing_csv_file')[0].files[0].name
    //validating that only csv files can be uploaded
    if (csv_file_name.slice(-3) != 'csv'){
        alert('Please upload csv files only!');
        return;
    }
    
    formData.append('csv_file', $('#id_existing_csv_file')[0].files[0]);
    $.ajax({
        url : "csv_file_upload/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            set_num_rels_exs(json['num_rels'], json['num_exs']);
            $('#num_rels').val(json['num_rels'])
            $('#num_exs').val(json['num_exs'])
            set_data(json['data']);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
});

function set_data(json){
    for(var i = 0; i < num_relse; i++){
        var rel = $('.relation_container').eq(i);
        rel.find('.relation_name').first().val(json[i]['name']);
        for(var j = 0; j < num_exse; j++){
            rel.find('.sentence').eq(j).val(json[i]['examples'][j]['sentence']);
            rel.find('.head').eq(j).val(json[i]['examples'][j]['head']);
            rel.find('.tail').eq(j).val(json[i]['examples'][j]['tail']);
        }   
    }
}

var num_relse = null;
var num_exse = null;

//helper function to resize the table as necessary.
function set_num_rels_exs(num_rels, num_exs){
    if(num_rels < 5 || num_rels == null){
        alert("Error there must be at least 5 relations!");
        return;
    }
    if(num_exs < 3 || num_exs == null){
        alert("Error there must be at least 3 examples per relation!");
        return;
    }
    num_relse = num_rels;
    num_exse = num_exs;
    var table_div = $('#table_container > div');
    if(table_div.length < num_rels){
        for(var i = table_div.length+1; i <= num_rels; i++){
            var new_rel = `<div class="mt-3 relation_container card">
            <div class="card-header">
                <label for="rel_name">Relation ` + i + ` Name: </label>
                <input type="text"  class="relation_name form-control"/>
            </div>
            <div class="example_container card-body">

            </div>
        </div>`;
            $('#table_container').append(new_rel);
        }
    }
    
    while($('#table_container > div').length > num_rels){
        $('#table_container').children().last().remove();
    }
    
    $('.example_container').each(function() {
        for(var i = $(this).children().length + 1; i <= num_exs; i++){
            var new_ex = `<div class="example">
            <p style="display:inline"> Example `+ i +` </p>
            <label> Sentence: </label>
            <input type="text" class="sentence form-control" />
            <label> Head: </label>
            <div class="col-3">
            <input type="text" class="head form-control" />
            </div>
            <label> Tail: </label>
            <div class="col-3">
            <input type="text" class="tail form-control" />
            </div>
            </div>`
            $(this).append(new_ex);
        }
        while($(this).children().length > num_exs){
            $(this).children().last().remove();
        }
    });
}

//Updates the table to specify the data based on the number of relations and the number of examples per relation.
$('#update_table').click(function() {
    var num_rels = $('#num_rels').val();
    var num_exs = $('#num_exs').val();
    set_num_rels_exs(num_rels, num_exs);
});

var headers = {
    sentence: "sentence",
    head: "head",
    tail: "tail",
    reldescription: "reldescription"
};

$('#download_as_csv').click(function() {
    json = [];
    for(var i = 0; i < num_relse; i++){
        var rel = $('.relation_container').eq(i);
        var rel_name = rel.find('.relation_name').first().val();
        for(var j = 0; j < num_exse; j++){
            ex_info = {}
            ex_info['sentence'] = "\"" + rel.find('.sentence').eq(j).val().replace(/["]/g, "\"\"") + "\"";
            ex_info['head'] = "\"" + rel.find('.head').eq(j).val().replace(/["]/g, "\"\"") + "\"";
            ex_info['tail'] = "\"" + rel.find('.tail').eq(j).val().replace(/["]/g, "\"\"") + "\"";
            ex_info['reldescription'] = "\"" + rel_name.replace(/["]/g, "\"\"") + "\"";
            json.push(ex_info);
        }   
    }
    exportCSVFile(headers, json, "relation_support_dataset.csv");
});


function convertToCSV(objArray) {
    var array = typeof objArray != 'object' ? JSON.parse(objArray) : objArray;
    var str = '';

    for (var i = 0; i < array.length; i++) {
        var line = '';
        for (var index in array[i]) {
            if (line != '') line += ','

            line += array[i][index];
        }

        str += line + '\r\n';
    }

    return str;
}

function exportCSVFile(headers, items, fileTitle) {
    if (headers) {
        items.unshift(headers);
    }

    // Convert Object to JSON
    var jsonObject = JSON.stringify(items);

    var csv = this.convertToCSV(jsonObject);

    var exportedFilenmae = fileTitle + '.csv' || 'export.csv';

    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    if (navigator.msSaveBlob) { // IE 10+
        navigator.msSaveBlob(blob, exportedFilenmae);
    } else {
        var link = document.createElement("a");
        if (link.download !== undefined) { // feature detection
            // Browsers that support HTML5 download attribute
            var url = URL.createObjectURL(blob);
            link.setAttribute("href", url);
            link.setAttribute("download", exportedFilenmae);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
}