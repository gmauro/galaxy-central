define(["libs/underscore"],function(c){function f(k,j,i){var l=new XMLHttpRequest();l.open("GET",k,true);l.setRequestHeader("Accept","application/json");l.setRequestHeader("Cache-Control","no-cache");l.setRequestHeader("X-Requested-With","XMLHttpRequest");l.onloadend=function(){var m=l.status;if(m==200){try{response=jQuery.parseJSON(l.responseText)}catch(n){response=l.responseText}j&&j(response)}else{i&&i(m)}};l.send()}function b(l,i){var j=$('<div class="'+l+'"></div>');j.appendTo(":eq(0)");var k=j.css(i);j.remove();return k}function a(i){if(!$('link[href^="'+i+'"]').length){$('<link href="'+galaxy_config.root+i+'" rel="stylesheet">').appendTo("head")}}function h(i,j){if(i){return c.defaults(i,j)}else{return j}}function d(j,l){var k="";if(j>=100000000000){j=j/100000000000;k="TB"}else{if(j>=100000000){j=j/100000000;k="GB"}else{if(j>=100000){j=j/100000;k="MB"}else{if(j>=100){j=j/100;k="KB"}else{if(j>0){j=j*10;k="b"}else{return"<strong>-</strong>"}}}}}var i=(Math.round(j)/10);if(l){return i+" "+k}else{return"<strong>"+i+"</strong> "+k}}function e(){return(new Date().getTime()).toString(36)}function g(j,l,n){for(var k in j){var m=j[k];if(m[l]==n){return m}}return{}}return{cssLoadFile:a,cssGetAttribute:b,jsonFromUrl:f,merge:h,bytesToString:d,uuid:e,findPair:g}});