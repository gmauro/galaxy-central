(function(){var b=Handlebars.template,a=Handlebars.templates=Handlebars.templates||{};a["template-history-historyPanel"]=b(function(l,A,y,r,I){this.compilerInfo=[2,">= 1.0.0-rc.3"];y=y||l.helpers;I=I||{};var z="",o,k,h,v=this,e="function",c=y.blockHelperMissing,d=this.escapeExpression;function u(N,M){var J="",L,K;J+='\n            <div id="history-name" class="tooltip editable-text"\n                title="';K={hash:{},inverse:v.noop,fn:v.program(2,t,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+='">';if(L=y.name){L=L.call(N,{hash:{},data:M})}else{L=N.name;L=typeof L===e?L.apply(N):L}J+=d(L)+"</div>\n            ";return J}function t(K,J){return"Click to rename history"}function s(N,M){var J="",L,K;J+='\n            <div id="history-name" class="tooltip"\n                title="';K={hash:{},inverse:v.noop,fn:v.program(5,q,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+='">';if(L=y.name){L=L.call(N,{hash:{},data:M})}else{L=N.name;L=typeof L===e?L.apply(N):L}J+=d(L)+"</div>\n            ";return J}function q(K,J){return"You must be logged in to edit your history name"}function p(N,M){var J="",L,K;J+='\n            <a id="history-tag" title="';K={hash:{},inverse:v.noop,fn:v.program(8,n,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+='"\n                class="icon-button tags tooltip" target="galaxy_main" href="javascript:void(0)"></a>\n            <a id="history-annotate" title="';K={hash:{},inverse:v.noop,fn:v.program(10,H,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+='"\n                class="icon-button annotate tooltip" target="galaxy_main" href="javascript:void(0)"></a>\n            ';return J}function n(K,J){return"Edit history tags"}function H(K,J){return"Edit history annotation"}function G(N,M){var J="",L,K;J+="\n    ";K={hash:{},inverse:v.noop,fn:v.program(13,F,M),data:M};if(L=y.warningmessagesmall){L=L.call(N,K)}else{L=N.warningmessagesmall;L=typeof L===e?L.apply(N):L}if(!y.warningmessagesmall){L=c.call(N,L,K)}if(L||L===0){J+=L}J+="\n    ";return J}function F(M,L){var K,J;J={hash:{},inverse:v.noop,fn:v.program(14,E,L),data:L};if(K=y.local){K=K.call(M,J)}else{K=M.local;K=typeof K===e?K.apply(M):K}if(!y.local){K=c.call(M,K,J)}if(K||K===0){return K}else{return""}}function E(K,J){return"You are currently viewing a deleted history!"}function D(N,M){var J="",L,K;J+='\n    <div id="history-tag-annotation">\n\n        <div id="history-tag-area" style="display: none">\n            <strong>';K={hash:{},inverse:v.noop,fn:v.program(17,C,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+=':</strong>\n            <div class="tag-elt"></div>\n        </div>\n\n        <div id="history-annotation-area" style="display: none">\n            <strong>';K={hash:{},inverse:v.noop,fn:v.program(19,B,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+=':</strong>\n            <div id="history-annotation-container">\n            <div id="history-annotation" class="tooltip editable-text"\n                title="';K={hash:{},inverse:v.noop,fn:v.program(21,m,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+='">\n                ';L=y["if"].call(N,N.annotation,{hash:{},inverse:v.program(25,i,M),fn:v.program(23,j,M),data:M});if(L||L===0){J+=L}J+="\n            </div>\n            </div>\n        </div>\n    </div>\n    ";return J}function C(K,J){return"Tags"}function B(K,J){return"Annotation"}function m(K,J){return"Click to edit annotation"}function j(M,L){var J="",K;J+="\n                    ";if(K=y.annotation){K=K.call(M,{hash:{},data:L})}else{K=M.annotation;K=typeof K===e?K.apply(M):K}J+=d(K)+"\n                ";return J}function i(N,M){var J="",L,K;J+="\n                    <em>";K={hash:{},inverse:v.noop,fn:v.program(26,g,M),data:M};if(L=y.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!y.local){L=c.call(N,L,K)}if(L||L===0){J+=L}J+="</em>\n                ";return J}function g(K,J){return"Describe or add notes to history"}function f(M,L){var J="",K;J+='\n    <div id="message-container">\n        <div class="';if(K=y.status){K=K.call(M,{hash:{},data:L})}else{K=M.status;K=typeof K===e?K.apply(M):K}J+=d(K)+'message">\n        ';if(K=y.message){K=K.call(M,{hash:{},data:L})}else{K=M.message;K=typeof K===e?K.apply(M):K}J+=d(K)+"\n        </div><br />\n    </div>\n    ";return J}function x(K,J){return"You are over your disk quota.\n            Tool execution is on hold until your disk usage drops below your allocated quota."}function w(K,J){return"Your history is empty. Click 'Get Data' on the left pane to start"}z+='<div id="history-controls">\n    <div id="history-title-area" class="historyLinks">\n\n        \n        <div id="history-name-container">\n            \n            ';k=y["if"].call(A,((o=A.user),o==null||o===false?o:o.email),{hash:{},inverse:v.program(4,s,I),fn:v.program(1,u,I),data:I});if(k||k===0){z+=k}z+='\n        </div>\n    </div>\n\n    <div id="history-subtitle-area">\n        <div id="history-size" style="float:left;">';if(k=y.nice_size){k=k.call(A,{hash:{},data:I})}else{k=A.nice_size;k=typeof k===e?k.apply(A):k}z+=d(k)+'</div>\n\n        <div id="history-secondary-links" style="float: right;">\n            ';k=y["if"].call(A,((o=A.user),o==null||o===false?o:o.email),{hash:{},inverse:v.noop,fn:v.program(7,p,I),data:I});if(k||k===0){z+=k}z+='\n        </div>\n        <div style="clear: both;"></div>\n    </div>\n\n    ';k=y["if"].call(A,A.deleted,{hash:{},inverse:v.noop,fn:v.program(12,G,I),data:I});if(k||k===0){z+=k}z+="\n\n    \n    \n    ";k=y["if"].call(A,((o=A.user),o==null||o===false?o:o.email),{hash:{},inverse:v.noop,fn:v.program(16,D,I),data:I});if(k||k===0){z+=k}z+="\n\n    ";k=y["if"].call(A,A.message,{hash:{},inverse:v.noop,fn:v.program(28,f,I),data:I});if(k||k===0){z+=k}z+='\n\n    <div id="quota-message-container" style="display: none">\n        <div id="quota-message" class="errormessage">\n            ';h={hash:{},inverse:v.noop,fn:v.program(30,x,I),data:I};if(k=y.local){k=k.call(A,h)}else{k=A.local;k=typeof k===e?k.apply(A):k}if(!y.local){k=c.call(A,k,h)}if(k||k===0){z+=k}z+='\n        </div>\n    </div>\n</div>\n\n<div id="';if(k=y.id){k=k.call(A,{hash:{},data:I})}else{k=A.id;k=typeof k===e?k.apply(A):k}z+=d(k)+'-datasets" class="history-datasets-list"></div>\n\n<div class="infomessagesmall" id="emptyHistoryMessage" style="display: none;">\n    ';h={hash:{},inverse:v.noop,fn:v.program(32,w,I),data:I};if(k=y.local){k=k.call(A,h)}else{k=A.local;k=typeof k===e?k.apply(A):k}if(!y.local){k=c.call(A,k,h)}if(k||k===0){z+=k}z+="\n</div>";return z})})();