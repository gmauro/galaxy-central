<%inherit file="/base.mako"/>
<%namespace file="/message.mako" import="render_msg" />

<%
    from galaxy import util
%>

%if message:
    ${render_msg( message, 'done' )}
%endif

<div class="toolForm">
    <div class="toolFormBody">
        <h3 align="center">Workflows per month for user "${util.restore_text( email )}"</h3>
        <table align="center" width="60%" class="colored">
            %if len( workflows ) == 0:
                <tr><td colspan="2">There are no workflows for user "${util.restore_text( email )}"</td></tr>
            %else:
                <tr class="header">
                    <td>Month</td>
                    <td>Total</td>
                </tr>
                <% ctr = 0 %>
                %for workflow in workflows:
                    <%
                        month = workflow[0]
                        total = workflow[1]
                    %>
                    %if ctr % 2 == 1:
                        <tr class="odd_row">
                    %else:
                        <tr class="tr">
                    %endif
                        <td>${month}</td>
                        <td>${total}</td>
                    </tr>
                    <% ctr += 1 %>
                %endfor
            %endif
        </table>
    </div>
</div>
