<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html>

<head>
<title>Galaxy History</title>

## This is now only necessary for tests
%if bool( [ data for data in history.active_datasets if data.state in ['running', 'queued', '', None ] ] ):
<!-- running: do not change this comment, used by TwillTestCase.wait -->
%endif

<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
<meta http-equiv="Pragma" content="no-cache">
<link href="${h.url_for('/static/style/base.css')}" rel="stylesheet" type="text/css" />
<link href="${h.url_for('/static/style/history.css')}" rel="stylesheet" type="text/css" />

## <!--[if lt IE 7]>
## <script defer type="text/javascript" src="/static/scripts/ie_pngfix.js"></script>
## <![endif]-->

<script type="text/javascript" src="${h.url_for('/static/scripts/jquery.js')}"></script>
<script type="text/javascript" src="${h.url_for('/static/scripts/jquery.cookie.js')}"></script>
<script type="text/javascript" src="${h.url_for('/static/scripts/cookie_set.js')}"></script>

<script type="text/javascript">
    var q = jQuery.noConflict();
    q( document ).ready( function() {
        initShowHide();
        setupHistoryItem( q("div.historyItemWrapper") );
        // Collapse all
        q("#top-links").append( "|&nbsp;" ).append( q("<a href='#'>collapse all</a>").click( function() {
            q( "div.historyItemBody:visible" ).each( function() {
                if ( q.browser.mozilla )
                {
                    q(this).find( "pre.peek" ).css( "overflow", "hidden" );
                }
                q(this).slideUp( "fast" );
            })
            var state = new CookieSet( "galaxy.history.expand_state" );
            state.removeAll().save();
	    return false;
        }));
    })
    // Functionized so AJAX'd datasets can call them
    // Get shown/hidden state from cookie
    function initShowHide() {
        q( "div.historyItemBody" ).hide();
        // Load saved state and show as neccesary
        var state = new CookieSet( "galaxy.history.expand_state" );
	for ( id in state.store ) { q( "#" + id ).children( "div.historyItemBody" ).show(); }
        // If Mozilla, hide scrollbars in hidden items since they cause animation bugs
        if ( q.browser.mozilla ) {
            q( "div.historyItemBody" ).each( function() {
                if ( ! q(this).is( ":visible" ) ) q(this).find( "pre.peek" ).css( "overflow", "hidden" );
            })
        }
        delete state;
    }
    // Add show/hide link and delete link to a history item
    function setupHistoryItem( query ) {
        query.each( function() {
            var id = this.id;
            var body = q(this).children( "div.historyItemBody" );
            var peek = body.find( "pre.peek" )
            q(this).children( ".historyItemTitleBar" ).find( ".historyItemTitle" ).wrap( "<a href='#'></a>" ).click( function() {
                if ( body.is(":visible") ) {
                    if ( q.browser.mozilla ) { peek.css( "overflow", "hidden" ) }
                    body.slideUp( "fast" );
                    ## other instances of this could be editing the cookie, refetch
                    var state = new CookieSet( "galaxy.history.expand_state" );
                    state.remove( id ); state.save();
                    delete state;
                } 
                else {
                    body.slideDown( "fast", function() { 
                        if ( q.browser.mozilla ) { peek.css( "overflow", "auto" ); } 
                    });
                    var state = new CookieSet( "galaxy.history.expand_state" );
                    state.add( id ); state.save();
                    delete state;
                }
		return false;
            });
            // Delete link
            q(this).find( "a.historyItemDelete" ).each( function() {
		var data_id = this.id.split( "-" )[1];
		q(this).click( function() {
		    q( '#progress-' + data_id ).show();
		    q.ajax({
			url: "${h.url_for( action='delete_async', id='XXX' )}".replace( 'XXX', data_id ),
			error: function() { alert( "Delete failed" ) },
			success: function() {
			    q( "#historyItem-" + data_id ).fadeOut( "fast", function() {
				q( "div#historyItemContainer-" + data_id ).remove();
				if ( q( "div.historyItemContainer" ).length < 1 ) {
				    q ( "div#emptyHistoryMessage" ).show();
				}
			    });
			}
		    });
		    return false;
		});
	    });
        });
    };
    // Looks for changes in dataset state using an async request. Keeps
    // calling itself (via setTimeout) until all datasets are in a terminal
    // state.
    var updater = function ( tracked_datasets ) {
        // Check if there are any items left to track
        var empty = true;
        for ( item in tracked_datasets ) {
            empty = false;
            break;
        }
        if ( ! empty ) {
            // console.log( "Updater running in 3 seconds" );
            setTimeout( function() { updater_callback( tracked_datasets ) }, 3000 );
        } else {
            // console.log( "Updater finished" );
        }
    };
    var updater_callback = function ( tracked_datasets ) {
        // Build request data
        var ids = []
        var states = []
        q.each( tracked_datasets, function ( id, state ) {
            ids.push( id );
            states.push( state );
        });
        // Make ajax call
        q.ajax( {
            type: "POST",
            url: "${h.url_for( controller='root', action='history_item_updates' )}",
            dataType: "json",
            data: { ids: ids.join( "," ), states: states.join( "," ) },
            success : function ( data ) {
                q.each( data, function( id, val ) {
                    // Replace HTML
                    var container = q("#historyItemContainer-" + id);
                    container.html( val.html );
                    setupHistoryItem( container.children( ".historyItemWrapper" ) );
                    initShowHide();
                    // If new state was terminal, stop tracking
                    if (( val.state == "ok") || ( val.state == "error") || ( val.state == "empty") || ( val.state == "deleted" )) {
                        delete tracked_datasets[ parseInt(id) ];
                    } else {
                        tracked_datasets[ parseInt(id) ] = val.state;
                    }
                });
                // Keep going (if there are still any items to track)
                updater( tracked_datasets );
            },
            error: function() {
                // Just retry, like the old method, should try to be smarter
                updater( tracked_datasets );
            }
        });
    };
</script>

<![if gte IE 7]>
<script type="text/javascript">
    q( document ).ready( function() {
        // Add rollover effect to any image with a 'rollover' attribute
        preload_images = {}
        q( "img[@rollover]" ).each( function() {
            var r = q(this).attr('rollover');
            var s = q(this).attr('src');
            preload_images[r] = true;
            q(this).hover( 
                function() { q(this).attr( 'src', r ) },
                function() { q(this).attr( 'src', s ) }
            )
        })
        for ( r in preload_images ) { q( "<img>" ).attr( "src", r ) }
    })
</script>
<![endif]>

<style type="text/css">
#footer {
    ## Netscape 4, IE 4.x-5.0/Win and other lesser browsers will use this
    position: absolute; left: 0px; bottom: 0px;
}
body > div#footer {
    ## used by Opera 5+, Netscape6+/Mozilla, Konqueror, Safari, OmniWeb 4.5+, iCab, ICEbrowser
    position: fixed;
}
</style>

<!--[if gte IE 5.5]>
<![if lt IE 7]>
<style type="text/css">
div#footer {
    /* IE5.5+/Win - this is more specific than the IE 5.0 version */
    width:100%;
    right: auto; bottom: auto;
    left: expression( ( -5 - footer.offsetWidth + ( document.documentElement.clientWidth ? document.documentElement.clientWidth : document.body.clientWidth ) + ( ignoreMe2 = document.documentElement.scrollLeft ? document.documentElement.scrollLeft : document.body.scrollLeft ) ) + 'px' );
    top: expression( ( - footer.offsetHeight + ( document.documentElement.clientHeight ? document.documentElement.clientHeight : document.body.clientHeight ) + ( ignoreMe = document.documentElement.scrollTop ? document.documentElement.scrollTop : document.body.scrollTop ) ) + 'px' );
}
</style>
<![endif]>
<![endif]-->

</head>

<body class="historyPage">

<div id="top-links" class="historyLinks">
    <a href="${h.url_for('history', show_deleted=show_deleted)}">refresh</a> 
    %if show_deleted:
    | <a href="${h.url_for('history', show_deleted=False)}">hide deleted</a> 
    %endif
</div>

%if history.deleted:
    <div class="warningmessagesmall">
        You are currently viewing a deleted history!
    </div>
    <p></p>
%endif

<%namespace file="history_common.mako" import="render_dataset" />

%if ( show_deleted and len( history.datasets ) < 1 ) or len( history.active_datasets ) < 1:
    <div class="infomessagesmall" id="emptyHistoryMessage">
%else:    
    <%
    if show_deleted:
        #all datasets
        datasets_to_show = history.activatable_datasets
    else:
        #active (not deleted)
        datasets_to_show = history.active_datasets
    %>
    ## Render requested datasets, ordered from newest to oldest
    %for data in reversed( datasets_to_show ):
        %if data.visible:
            <div class="historyItemContainer" id="historyItemContainer-${data.id}">
                ${render_dataset( data, data.hid )}
            </div>
        %endif
    %endfor
    <script type="text/javascript">
    var tracked_datasets = {};
    %for data in reversed( history.active_datasets ):
        %if data.visible and data.state not in [ "deleted", "empty", "error", "ok" ]:
            tracked_datasets[ ${data.id} ] = "${data.state}";
        %endif
    %endfor
    updater( tracked_datasets );
    </script>
    <div class="infomessagesmall" id="emptyHistoryMessage" style="display:none;">
%endif
        Your history is empty. Click 'Get Data' on the left pane to start
    </div>

</body>
</html>
