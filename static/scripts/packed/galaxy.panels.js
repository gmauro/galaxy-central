var hidden_width=7;var border_tweak=jQuery.browser.msie?14:9;var jq=jQuery;function ensure_dd_helper(){if(jq("#DD-helper").length==0){var A=jq("<div id='DD-helper' style='background: white; opacity: 0.00; top: 0; left: 0; width: 100%; height: 100%; position: absolute; z-index: 9000;'></div>");if(jq.browser.ie){A.css("opacity","0.01")}A.appendTo("body").hide()}}function make_left_panel(E,A,B){var D=false;var C=null;resize=function(F){var G=F;if(F<0){F=0}jq(E).css("width",F);jq(B).css("left",G);jq(A).css("left",F+7)};toggle=function(){if(D){jq(B).removeClass("hover");jq(B).animate({left:C},"fast");jq(E).css("left",-C).show().animate({"left":0},"fast",function(){resize(C);jq(B).removeClass("hidden")});D=false}else{C=jq(B).position().left;jq(A).css("left",hidden_width);jq(B).removeClass("hover");jq(E).animate({left:-C},"fast");jq(B).animate({left:-1},"fast",function(){jq(this).addClass("hidden")});D=true}};jq(B).hover(function(){jq(this).addClass("hover")},function(){jq(this).removeClass("hover")}).draggable({start:function(F,G){jq("#DD-helper").show()},stop:function(F,G){jq("#DD-helper").hide();return false},drag:function(F,G){x=G.position.left;x=Math.min(400,Math.max(100,x));if(D){jq(E).css("left",0);jq(B).removeClass("hidden");D=false}resize(x);G.draggable.pos[0]=x;G.draggable.pos[1]=G.options.co.top},click:function(){toggle()}}).find("div").show()}function make_right_panel(A,E,G){var I=false;var F=false;var C=null;var D=function(J){jq(A).css("width",J);jq(E).css("right",J+9);jq(G).css("right",J).css("left","")};var H=function(){if(I){jq(G).removeClass("hover");jq(G).animate({right:C},"fast");jq(A).css("right",-C).show().animate({"right":0},"fast",function(){D(C);jq(G).removeClass("hidden")});I=false}else{C=jq(document).width()-jq(G).position().left-border_tweak;jq(E).css("right",hidden_width+1);jq(G).removeClass("hover");jq(A).animate({right:-C},"fast");jq(G).animate({right:-1},"fast",function(){jq(this).addClass("hidden")});I=true}F=false};var B=function(J){var K=jq(E).width()-(I?C:0);if(K<J){if(!I){H();F=true}}else{if(F){H();F=false}}};jq(G).hover(function(){jq(this).addClass("hover")},function(){jq(this).removeClass("hover")}).draggable({start:function(J,K){jq("#DD-helper").show()},stop:function(J,K){x=K.position.left;w=jq(window).width();x=Math.min(w-100,x);x=Math.max(w-400,x);D(w-x-border_tweak);jq("#DD-helper").hide();return false},click:function(){H()},drag:function(J,K){x=K.position.left;w=jq(window).width();x=Math.min(w-100,x);x=Math.max(w-400,x);if(I){jq(A).css("right",0);jq(G).removeClass("hidden");I=false}D(w-x-border_tweak);K.draggable.pos[0]=x;K.draggable.pos[1]=K.options.co.top}}).find("div").show();return{handle_minwidth_hint:B}}