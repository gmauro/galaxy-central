function ensure_dd_helper(){if($("#DD-helper").length==0){$("<div id='DD-helper'/>").css({background:"white",opacity:0,zIndex:9000,position:"absolute",top:0,left:0,width:"100%",height:"100%"}).appendTo("body").hide()}}function make_left_panel(h,c,e){var g=false;var f=null;var d=function(i){var j=i;if(i<0){i=0}$(h).css("width",i);$(e).css("left",j);$(c).css("left",i+7);if(document.recalc){document.recalc()}};var a=function(){if(g){$(e).removeClass("hover");$(e).animate({left:f},"fast");$(h).css("left",-f).show().animate({left:0},"fast",function(){d(f);$(e).removeClass("hidden")});g=false}else{f=$(e).position().left;$(c).css("left",$(e).innerWidth());if(document.recalc){document.recalc()}$(e).removeClass("hover");$(h).animate({left:-f},"fast");$(e).animate({left:-1},"fast",function(){$(this).addClass("hidden")});g=true}};$(e).hover(function(){$(this).addClass("hover")},function(){$(this).removeClass("hover")}).bind("dragstart",function(i){$("#DD-helper").show()}).bind("dragend",function(i){$("#DD-helper").hide()}).bind("drag",function(i){x=i.offsetX;x=Math.min(400,Math.max(100,x));if(g){$(h).css("left",0);$(e).removeClass("hidden");g=false}d(x)}).bind("dragclickonly",function(i){a()}).find("div").show();var b=function(i){if((g&&i=="show")||(!g&&i=="hide")){a()}};return{force_panel:b}}function make_right_panel(a,e,h){var j=false;var g=false;var c=null;var d=function(k){$(a).css("width",k);$(e).css("right",k+9);$(h).css("right",k).css("left","");if(document.recalc){document.recalc()}};var i=function(){if(j){$(h).removeClass("hover");$(h).animate({right:c},"fast");$(a).css("right",-c).show().animate({right:0},"fast",function(){d(c);$(h).removeClass("hidden")});j=false}else{c=$(document).width()-$(h).position().left-$(h).outerWidth();$(e).css("right",$(h).innerWidth()+1);if(document.recalc){document.recalc()}$(h).removeClass("hover");$(a).animate({right:-c},"fast");$(h).animate({right:-1},"fast",function(){$(this).addClass("hidden")});j=true}g=false};var b=function(k){var l=$(e).width()-(j?c:0);if(l<k){if(!j){i();g=true}}else{if(g){i();g=false}}};$(h).hover(function(){$(this).addClass("hover")},function(){$(this).removeClass("hover")}).bind("dragstart",function(k){$("#DD-helper").show()}).bind("dragend",function(k){$("#DD-helper").hide()}).bind("drag",function(k){x=k.offsetX;w=$(window).width();x=Math.min(w-100,x);x=Math.max(w-400,x);if(j){$(a).css("right",0);$(h).removeClass("hidden");j=false}d(w-x-$(this).outerWidth())}).bind("dragclickonly",function(k){i()}).find("div").show();var f=function(k){if((j&&k=="show")||(!j&&k=="hide")){i()}};return{handle_minwidth_hint:b,force_panel:f}}function hide_modal(){$(".dialog-box-container").fadeOut(function(){$("#overlay").hide();$(".dialog-box").find(".body").children().remove()})}function show_modal(f,c,e,d){if(f){$(".dialog-box").find(".title").html(f);$(".dialog-box").find(".unified-panel-header").show()}else{$(".dialog-box").find(".unified-panel-header").hide()}var a=$(".dialog-box").find(".buttons").html("");if(e){$.each(e,function(b,g){a.append($("<button/>").text(b).click(g));a.append(" ")});a.show()}else{a.hide()}var a=$(".dialog-box").find(".extra_buttons").html("");if(d){$.each(d,function(b,g){a.append($("<button/>").text(b).click(g));a.append(" ")});a.show()}else{a.hide()}if(c=="progress"){c=$("<img src='../images/yui/rel_interstitial_loading.gif')' />")}$(".dialog-box").find(".body").html(c);if(!$(".dialog-box-container").is(":visible")){$("#overlay").show();$(".dialog-box-container").fadeIn()}}function show_in_overlay(c){var d=c.width||"600";var b=c.height||"400";var a=c.scroll||"auto";$("#overlay-background").bind("click.overlay",function(){hide_modal();$("#overlay-background").unbind("click.overlay")});show_modal(null,$("<div style='margin: -5px;'><img id='close_button' style='position:absolute;right:-17px;top:-15px;' src='../images/closebox.png'><iframe style='margin: 0; padding: 0;' src='"+c.url+"' width='"+d+"' height='"+b+"' scrolling='"+a+"' frameborder='0'></iframe></div>"));$("#close_button").bind("click",function(){hide_modal()})}$(function(){$(".tab").each(function(){var a=$(this).children(".submenu");if(a.length>0){if($.browser.msie){a.prepend("<iframe style=\"position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; filter:Alpha(Opacity='0');\"></iframe>")}$(this).hover(function(){a.show()},function(){a.hide()});a.click(function(){a.hide()})}})});function user_changed(a,b){if(a){$(".loggedin-only").show();$(".loggedout-only").hide();$("#user-email").text(a);if(b){$(".admin-only").show()}}else{$(".loggedin-only").hide();$(".loggedout-only").show();$(".admin-only").hide()}};