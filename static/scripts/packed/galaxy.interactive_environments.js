function append_notebook(a){clear_main_area();$("#main").append('<iframe frameBorder="0" seamless="seamless" style="width: 100%; height: 100%; overflow:hidden;" scrolling="no" src="'+a+'"></iframe>')}function clear_main_area(){$("#spinner").remove();$("#main").children().remove()}function display_spinner(){$("#main").append('<img id="spinner" src="'+galaxy_root+'/static/style/largespinner.gif" style="position:absolute;margin:auto;top:0;left:0;right:0;bottom:0;">')}function test_ie_availability(b,c){var a=0;display_spinner();interval=setInterval(function(){$.ajax({url:b,xhrFields:{withCredentials:true},type:"GET",timeout:500,success:function(){console.log("Connected to IE, returning");clearInterval(interval);c()},error:function(f,d,e){a++;console.log("Request "+a);if(a>30){clearInterval(interval);clear_main_area();toastr.error("Could not connect to IE, contact your administrator","Error",{closeButton:true,timeOut:20000,tapToDismiss:false})}}})},1000)};