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
    $("#sna_viz_nav").addClass("active");
});

do_check_request = false;
function start_success_check(json) {
    if (json.hasOwnProperty('status')){
        $("#node_link_viz").html('');
        alert('Generating Graph! Please Wait!');
        setTimeout(check_analysis_results, 3000);
        do_check_request = true;
    }else{
        alert('Error!');
    }
}

function check_analysis_results() {
    $.ajax({
        url : "gen_node_link/", // the endpoint
        type : "GET", // http method
 
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            if(json.hasOwnProperty('error')){
                do_check_request = false;
                alert('Error!');
                return;
            }
            if(json.status == "finished"){
                do_check_request = false;
                $("#node_link_viz").load("../static/node_link_viz.html"); 
            }
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        },
        
        complete: function() {
            // Schedule the next request when the current one's complete, even if it fails
            if(do_check_request){
                setTimeout(check_analysis_results, 2000);
            }
        }
    });
}

//when the generate node link graph button is clicked
$('#gen_node_link_graph').click(function(){
    
    $.ajax({
        url : "gen_node_link/", // the endpoint
        type : "POST", // http method
 
        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            start_success_check(json);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
    
});