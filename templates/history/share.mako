<%inherit file="/base.mako"/>
<%def name="title()">Share histories</%def>

%if not can_change and not cannot_change:
<div class="toolForm">
<div class="toolFormTitle">Share Histories</div>
<table>
<form action="${h.url_for( action='history_share' )}" method="post" >
    <tr><th>History Name:</td><th>Number of Datasets:</th><th>Share Link</th></tr>
    %for history in histories:
    <tr><td align="center">${history.name}<input type="hidden" name="id" value="${history.id}"></td><td align="center">
    
    %if len(history.datasets) < 1:
    <div class="warningmark">
	This history contains no data.
    </div>
    %else:
    ${len(history.datasets)}
    %endif
    </td>
    <td align="center"><a href="${h.url_for( action='history_import', id=history.id )}">copy link to share</a></td>
    </tr>
    %endfor
    <tr><td>Email of User to share with:</td><td><input type="text" name="email" value="${email}" size="40"></td></tr>
    %if send_to_err:
    <tr><td colspan="100%"><div class="errormessage">${send_to_err}</div></td></tr>
    %endif
    <tr><td colspan="2" align="right"><input type="submit" name="history_share_btn" value="Submit"></td></tr>
</form>
</table>
</div>
%else:
<style type="text/css">
    th
    {
        text-align: left;
    }
    td
    {
        vertical-align: top;
    }
</style>
<form action="${h.url_for( action='history_share' )}" method="post">
    %for history in histories:
        <input type="hidden" name="id" value="${history.id}">
    %endfor
    <input type="hidden" name="email" value="${email}">
        <div class="warningmessage">
        The history or histories you've chosen to share contain datasets that the user you're sharing with does not have permission to access.  These datasets are shown below.  Datasets which the user already has permission to access are not shown.
        </div>
        <p/>
        %if can_change:
            <div class="donemessage">
                The following datasets can be shared with ${email} by updating their permissions:
                <p/>
                <table cellpadding="0" cellspacing="8" border="0">
                    <tr><th>Histories</th><th>Datasets</th></tr>
                    %for history, datasets in can_change.items():
                        <tr>
                            <td>${history.name}</td>
                            <td>
                                %for dataset in datasets:
                                    ${dataset.name}<br/>
                                %endfor
                            </td>
                        </tr>
                    %endfor
                </table>
            </div>
            <p/>
        %endif
        %if cannot_change:
            <div class="errormessage">
                The following datasets cannot be shared with ${email} because you do not have permission to change the permissions on them.
                <p/>
                <table cellpadding="0" cellspacing="8" border="0">
                    <tr><th>Histories</th><th>Datasets</th></tr>
                    %for history, datasets in cannot_change.items():
                        <tr>
                            <td>${history.name}</td>
                            <td>
                                %for dataset in datasets:
                                    ${dataset.name}<br/>
                                %endfor
                            </td>
                        </tr>
                    %endfor
                </table>
            </div>
            <p/>
        %endif
    <div>
        <b>How would you like to proceed?</b>
        <p/>
        %if can_change:
            <input type="radio" name="action" value="update"> Change permissions
            %if cannot_change:
                (where possible)
            %endif
            <br/>
        %endif
        <input type="radio" name="action" value="share"> Share anyway
        %if can_change:
            (don't change any permissions)
        %endif
        <br/>
        <input type="radio" name="action" value="no_share"> Don't share<br/>
        <br/>
        <input type="submit" name="submit" value="Ok"><br/>
    </div>
</form>
%endif
