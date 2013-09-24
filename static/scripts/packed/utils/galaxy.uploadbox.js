(function(g){jQuery.event.props.push("dataTransfer");var c={url:"",paramname:"content",maxfilesize:250,dragover:function(){},dragleave:function(){},announce:function(){},initialize:function(){},progress:function(){},success:function(){},error:function(i,j,k){alert(k)},complete:function(){},error_browser:"Your browser does not support drag-and-drop file uploads.",error_filesize:"This file is too large (>250MB). Please use an FTP client to upload it.",error_default:"Please make sure the file is available."};var f={};var a={};var b=0;var d=0;var h=false;var e=null;g.fn.uploadbox=function(x){f=g.extend({},c,x);e=this;e.append('<input id="uploadbox_input" type="file" style="display: none" multiple>');e.on("drop",l);e.on("dragover",m);e.on("dragleave",t);g("#uploadbox_input").change(function(y){v(y.target.files)});function l(y){if(!y.dataTransfer){return}v(y.dataTransfer.files);y.preventDefault();return false}function m(y){y.preventDefault();f.dragover.call(y)}function t(y){y.stopPropagation();f.dragleave.call(y)}function i(y){if(y.lengthComputable){f.progress(this.index,this.file,Math.round((y.loaded*100)/y.total))}}function v(A){if(h){return}for(var z=0;z<A.length;z++){var y=String(b++);a[y]=A[z];d++;f.announce(y,a[y],"")}}function o(y){if(a[y]){delete a[y];d--}}function j(){if(d==0){h=false;f.complete();return}else{h=true}var B=-1;for(var D in a){B=D;break}var C=a[B];o(B);var F=f.initialize(B,C);try{var z=new FileReader();var A=C.size;var y=1048576*f.maxfilesize;z.index=B;if(A<y){z.onload=function(G){n(B,C,F)};z.onerror=function(G){r(B,C,f.error_default)};z.readAsDataURL(C)}else{r(B,C,f.error_filesize)}}catch(E){r(B,C,E)}}function n(y,A,B){var C=new FormData();for(var z in B){C.append(z,B[z])}C.append(f.paramname,A,A.name);var D=new XMLHttpRequest();D.upload.index=y;D.upload.file=A;D.upload.addEventListener("progress",i,false);D.open("POST",f.url,true);D.setRequestHeader("Accept","application/json");D.setRequestHeader("Cache-Control","no-cache");D.setRequestHeader("X-Requested-With","XMLHttpRequest");D.send(C);D.onloadend=function(){var E=null;if(D.responseText){try{E=jQuery.parseJSON(D.responseText)}catch(F){E=D.responseText}}if(D.status<200||D.status>299){var G=D.statusText;if(!D.statusText){G=f.error_default}r(y,A,G+" (Server Code "+D.status+")")}else{u(y,A,E)}}}function u(y,z,A){f.success(y,z,A);j()}function r(y,z,A){f.error(y,z,A);j()}function s(){g("#uploadbox_input").trigger("click")}function q(y){for(y in a){o(y)}}function w(){if(!h){j()}}function k(y){f=g.extend({},f,y);return f}function p(){return window.File&&window.FileReader&&window.FormData&&window.XMLHttpRequest}return{select:s,remove:o,upload:w,reset:q,configure:k,compatible:p}}})(jQuery);