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


// called when the file upload button is clicked
$('#rel_ex_files_form').on('submit', function(event){
    event.preventDefault();
    var formData = new FormData();
    var sup_dataset_name = $('#id_relation_support_dataset')[0].files[0].name
    var queries_name = $('#id_queries_dataset')[0].files[0].name
    //validating that only csv files can be uploaded
    if (sup_dataset_name.slice(-3) != 'csv' || queries_name.slice(-3) != 'csv'){
        alert('Please upload csv files only!');
        return;
    }
    
    
    formData.append('relation_support_dataset', $('#id_relation_support_dataset')[0].files[0]);
    formData.append('queries_dataset', $('#id_queries_dataset')[0].files[0]);
    $.ajax({
        url : "rel_ex_files/", // the endpoint
        type : "POST", // http method
        data : formData,
        processData: false,
        contentType: false,

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            alert('Files successfully uploaded!');
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
});

//Does GET results periodically to load the results of the analysis.
function check_analysis_results() {
    $.ajax({
        url: "get_analysis_results/",
        type: "GET",
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            //TODO
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        },
        
        complete: function() {
            // Schedule the next request when the current one's complete
            setTimeout(check_analysis_results, 1000);
        }
    });
}

//When the do analysis button is clicked
$('#do_analysis_button').click(function() {
    $.ajax({
        url: "start_analysis/",
        type: "GET",
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            alert('Started analysis successfully!');
            setTimeout(check_analysis_results, 3000);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
});
