(function(){var b=Handlebars.template,a=Handlebars.templates=Handlebars.templates||{};a["template-history-historyPanel"]=b(function(m,C,A,s,J){this.compilerInfo=[4,">= 1.0.0"];A=this.merge(A,m.helpers);J=J||{};var B="",p,l,h,x=this,e="function",c=A.blockHelperMissing,d=this.escapeExpression;function v(O,N){var K="",M,L;K+='\n            <div id="history-name" class="tooltip editable-text"\n                title="';L={hash:{},inverse:x.noop,fn:x.program(2,u,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+='">';if(M=A.name){M=M.call(O,{hash:{},data:N})}else{M=O.name;M=typeof M===e?M.apply(O):M}K+=d(M)+"</div>\n            ";return K}function u(L,K){return"Click to rename history"}function t(O,N){var K="",M,L;K+='\n            <div id="history-name" class="tooltip"\n                title="';L={hash:{},inverse:x.noop,fn:x.program(5,r,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+='">';if(M=A.name){M=M.call(O,{hash:{},data:N})}else{M=O.name;M=typeof M===e?M.apply(O):M}K+=d(M)+"</div>\n            ";return K}function r(L,K){return"You must be logged in to edit your history name"}function q(O,N){var K="",M,L;K+='\n            <a id="history-tag" title="';L={hash:{},inverse:x.noop,fn:x.program(8,o,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+='"\n                class="icon-button tags tooltip" target="galaxy_main" href="javascript:void(0)"></a>\n            <a id="history-annotate" title="';L={hash:{},inverse:x.noop,fn:x.program(10,I,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+='"\n                class="icon-button annotate tooltip" target="galaxy_main" href="javascript:void(0)"></a>\n            ';return K}function o(L,K){return"Edit history tags"}function I(L,K){return"Edit history annotation"}function H(O,N){var K="",M,L;K+='\n    <div id="history-tag-annotation">\n\n        <div id="history-tag-area" style="display: none">\n            <strong>';L={hash:{},inverse:x.noop,fn:x.program(13,G,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+=':</strong>\n            <div class="tag-elt"></div>\n        </div>\n\n        <div id="history-annotation-area" style="display: none">\n            <strong>';L={hash:{},inverse:x.noop,fn:x.program(15,F,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+=':</strong>\n            <div id="history-annotation-container">\n            <div id="history-annotation" class="tooltip editable-text"\n                title="';L={hash:{},inverse:x.noop,fn:x.program(17,E,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+='">\n                ';M=A["if"].call(O,O.annotation,{hash:{},inverse:x.program(21,n,N),fn:x.program(19,D,N),data:N});if(M||M===0){K+=M}K+="\n            </div>\n            </div>\n        </div>\n    </div>\n    ";return K}function G(L,K){return"Tags"}function F(L,K){return"Annotation"}function E(L,K){return"Click to edit annotation"}function D(N,M){var K="",L;K+="\n                    ";if(L=A.annotation){L=L.call(N,{hash:{},data:M})}else{L=N.annotation;L=typeof L===e?L.apply(N):L}K+=d(L)+"\n                ";return K}function n(O,N){var K="",M,L;K+="\n                    <em>";L={hash:{},inverse:x.noop,fn:x.program(22,k,N),data:N};if(M=A.local){M=M.call(O,L)}else{M=O.local;M=typeof M===e?M.apply(O):M}if(!A.local){M=c.call(O,M,L)}if(M||M===0){K+=M}K+="</em>\n                ";return K}function k(L,K){return"Describe or add notes to history"}function j(O,N){var K="",M,L;K+="\n    ";L={hash:{},inverse:x.noop,fn:x.program(25,i,N),data:N};if(M=A.warningmessagesmall){M=M.call(O,L)}else{M=O.warningmessagesmall;M=typeof M===e?M.apply(O):M}if(!A.warningmessagesmall){M=c.call(O,M,L)}if(M||M===0){K+=M}K+="\n    ";return K}function i(N,M){var L,K;K={hash:{},inverse:x.noop,fn:x.program(26,g,M),data:M};if(L=A.local){L=L.call(N,K)}else{L=N.local;L=typeof L===e?L.apply(N):L}if(!A.local){L=c.call(N,L,K)}if(L||L===0){return L}else{return""}}function g(L,K){return"You are currently viewing a deleted history!"}function f(N,M){var K="",L;K+='\n        <div class="';if(L=A.status){L=L.call(N,{hash:{},data:M})}else{L=N.status;L=typeof L===e?L.apply(N):L}K+=d(L)+'message">';if(L=A.message){L=L.call(N,{hash:{},data:M})}else{L=N.message;L=typeof L===e?L.apply(N):L}K+=d(L)+"</div>\n        ";return K}function z(L,K){return"You are over your disk quota"}function y(L,K){return"Tool execution is on hold until your disk usage drops below your allocated quota"}function w(L,K){return"Your history is empty. Click 'Get Data' on the left pane to start"}B+='<div id="history-controls">\n\n    <div id="history-title-area" class="historyLinks">\n        \n        <div id="history-name-container">\n            \n            ';l=A["if"].call(C,((p=C.user),p==null||p===false?p:p.email),{hash:{},inverse:x.program(4,t,J),fn:x.program(1,v,J),data:J});if(l||l===0){B+=l}B+='\n        </div>\n    </div>\n\n    <div id="history-subtitle-area">\n        <div id="history-size" style="float:left;">';if(l=A.nice_size){l=l.call(C,{hash:{},data:J})}else{l=C.nice_size;l=typeof l===e?l.apply(C):l}B+=d(l)+'</div>\n\n        <div id="history-secondary-links" style="float: right;">\n            ';l=A["if"].call(C,((p=C.user),p==null||p===false?p:p.email),{hash:{},inverse:x.noop,fn:x.program(7,q,J),data:J});if(l||l===0){B+=l}B+='\n        </div>\n        <div style="clear: both;"></div>\n    </div>\n\n    \n    \n    ';l=A["if"].call(C,((p=C.user),p==null||p===false?p:p.email),{hash:{},inverse:x.noop,fn:x.program(12,H,J),data:J});if(l||l===0){B+=l}B+="\n\n    ";l=A["if"].call(C,C.deleted,{hash:{},inverse:x.noop,fn:x.program(24,j,J),data:J});if(l||l===0){B+=l}B+='\n\n    <div id="message-container">\n        ';l=A["if"].call(C,C.message,{hash:{},inverse:x.noop,fn:x.program(28,f,J),data:J});if(l||l===0){B+=l}B+='\n    </div>\n\n    <div id="quota-message-container" style="display: none">\n        <div id="quota-message" class="errormessage">\n            ';h={hash:{},inverse:x.noop,fn:x.program(30,z,J),data:J};if(l=A.local){l=l.call(C,h)}else{l=C.local;l=typeof l===e?l.apply(C):l}if(!A.local){l=c.call(C,l,h)}if(l||l===0){B+=l}B+=".\n            ";h={hash:{},inverse:x.noop,fn:x.program(32,y,J),data:J};if(l=A.local){l=l.call(C,h)}else{l=C.local;l=typeof l===e?l.apply(C):l}if(!A.local){l=c.call(C,l,h)}if(l||l===0){B+=l}B+='.\n        </div>\n    </div>\n</div>\n\n<div id="';if(l=A.id){l=l.call(C,{hash:{},data:J})}else{l=C.id;l=typeof l===e?l.apply(C):l}B+=d(l)+'-datasets" class="history-datasets-list"></div>\n\n<div class="infomessagesmall" id="emptyHistoryMessage" style="display: none;">\n    ';h={hash:{},inverse:x.noop,fn:x.program(34,w,J),data:J};if(l=A.local){l=l.call(C,h)}else{l=C.local;l=typeof l===e?l.apply(C):l}if(!A.local){l=c.call(C,l,h)}if(l||l===0){B+=l}B+="\n</div>";return B})})();