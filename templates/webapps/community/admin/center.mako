<%inherit file="/base.mako"/>

<%def name="title()">Galaxy Administration</%def>

<h2>Administration</h2>

<p>The menu on the left provides the following features</p>
<ul>
    <li><strong>Security</strong> - see the <strong>Data Security and Data Libraries</strong> section below for details
        <p/>
        <ul>
            <li>
                <strong>Manage users</strong> - provides a view of the registered users and all groups and non-private roles associated 
                with each user.  
            </li>
            <p/>
            <li>
                <strong>Manage groups</strong> - provides a view of all groups along with the members of the group and the roles associated with
                each group (both private and non-private roles).  The group names include a link to a page that allows you to manage the users and 
                roles that are associated with the group.
            </li>
            <p/>
            <li>
                <strong>Manage roles</strong> - provides a view of all non-private roles along with the role type, and the users and groups that
                are associated with the role.  The role names include a link to a page that allows you to manage the users and groups that are associated 
                with the role.  The page also includes a view of the data library datasets that are associated with the role and the permissions applied 
                to each dataset.
            </li>
        </ul>
    </li>
    <p/>
    <li><strong>Tools</strong>
        <p/>
        <ul>
            <li>
                <strong>Manage tools</strong> - coming soon...
            </li>
        </ul>
    </li>
</ul>
<br/>
