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
    $("#saved_results_nav").addClass("active");
});

var selected_timestamp_tracker = null;

//When the retrieve results button is clicked
$('#retrieve_result_button').click(function() {
    selected_timestamp_tracker = $("#timestamp_selector").val();
    if(selected_timestamp_tracker != null){
        $.ajax({
            url : "get/", // the endpoint
            type : "GET", // http method
            data : {'source_id': $("#timestamp_selector").val()},

            // handle a successful response
            success : function(json) {
                console.log(json); // log the returned json to the console
                var new_data = json.data;
                $('#result_table').html('');
                for(var i = 0; i < new_data.length; i++){
                    $('#result_table').append('<tr><td>'+new_data[i].sentence+'</td> <td class="align-middle">'+new_data[i].head+'</td><td class="align-middle">'+new_data[i].tail+'</td><td>'+new_data[i].pred_relation+'</td><td>'+new_data[i].pred_sentiment+'</td><td>'+new_data[i].conf.toString()+"%"+'</td></tr>');
                }
            },

            // handle a non-successful response
            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
            }
        }); 
    }
   
});

//when the retrieve all results button is clicked. 
$('#retrieve_all_result_button').click(function() {
    var link = document.createElement('a');
    link.href = "/saved_results/dwn_all/";
    link.download = "all_analysis_results.csv";
    link.click();
});

//When the download results as csv button is clicked
$('#download_results_csv').click(function() {
    if(selected_timestamp_tracker != null){
        var link = document.createElement('a');
        link.href = "/saved_results/get_csv/?source_id="+selected_timestamp_tracker;
        link.download = "analysis_results.csv";
        link.click();
    }
});

//when the button is clicked to upload the csv with relation ids to delete
$('#del_csv_form').on('submit', function(){
    event.preventDefault();
    var formData = new FormData();
    var dataset_name = $('#id_delete_rels_csv')[0].files[0].name
    //validating that only csv files can be uploaded
    if (dataset_name.slice(-3) != 'csv'){
        alert('Please upload csv files only!');
        return;
    }
    
    
    formData.append('dataset', $('#id_delete_rels_csv')[0].files[0]);
    $.ajax({
        url : "del_csv/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            if(json.status == "error"){
                alert('Error!');
                return;
            }
            alert('Deleted successfully!');
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
});