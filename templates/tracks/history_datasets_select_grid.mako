<%inherit file="/tracks/history_select_grid.mako"/>

<%def name="title()">
    ##
    ## Provide link to go back to histories grid.
    ##
    <%
        url_dict = dict( action="list_histories" )
        for filter, value in grid.cur_filter_dict.iteritems():
            url_dict[ "f-" + filter ] = value
    %>
    ## Use class 'label' to piggyback on URL functionality in parent template.
    <a class="label" href="${h.url_for( **url_dict )}">Back to histories</a><br/>
    ${parent.title()}
</%def>