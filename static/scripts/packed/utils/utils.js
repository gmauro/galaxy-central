define(["libs/underscore"],function(j){function d(l,m,k){g("GET",l,{},m,k)}function g(p,l,m,o,k){if(p=="GET"||p=="DELETE"){if(l.indexOf("?")==-1){l+="?"}else{l+="&"}l+=$.param(m)}var n=new XMLHttpRequest();n.open(p,l,true);n.setRequestHeader("Accept","application/json");n.setRequestHeader("Cache-Control","no-cache");n.setRequestHeader("X-Requested-With","XMLHttpRequest");n.setRequestHeader("Content-Type","application/json");n.onloadend=function(){var q=n.status;try{response=jQuery.parseJSON(n.responseText)}catch(r){response=n.responseText}if(q==200){o&&o(response)}else{k&&k(response)}};if(p=="GET"||p=="DELETE"){n.send()}else{n.send(JSON.stringify(m))}}function h(n,k){var l=$('<div class="'+n+'"></div>');l.appendTo(":eq(0)");var m=l.css(k);l.remove();return m}function f(k){if(!$('link[href^="'+k+'"]').length){$('<link href="'+galaxy_config.root+k+'" rel="stylesheet">').appendTo("head")}}function i(k,l){if(k){return j.defaults(k,l)}else{return l}}function b(l,n){var m="";if(l>=100000000000){l=l/100000000000;m="TB"}else{if(l>=100000000){l=l/100000000;m="GB"}else{if(l>=100000){l=l/100000;m="MB"}else{if(l>=100){l=l/100;m="KB"}else{if(l>0){l=l*10;m="b"}else{return"<strong>-</strong>"}}}}}var k=(Math.round(l)/10);if(n){return k+" "+m}else{return"<strong>"+k+"</strong> "+m}}function a(){return(new Date().getTime()).toString(36)}function c(k){var l=$("<p></p>");l.append(k);return l}function e(){var m=new Date();var k=(m.getHours()<10?"0":"")+m.getHours();var l=(m.getMinutes()<10?"0":"")+m.getMinutes();var n=m.getDate()+"/"+(m.getMonth()+1)+"/"+m.getFullYear()+", "+k+":"+l;return n}return{cssLoadFile:f,cssGetAttribute:h,get:d,merge:i,bytesToString:b,uuid:a,time:e,wrap:c,request:g}});