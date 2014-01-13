/*
    galaxy menu
*/

// dependencies
define(["galaxy.masthead"], function(mod_masthead) {

// frame manager
var GalaxyMenu = Backbone.Model.extend(
{
    // options
    options: null,
    
    // link masthead class
    masthead: null,
    
    // initialize
    initialize: function(options)
    {
        this.options = options.config;
        this.masthead  = options.masthead;
        this.create();
    },
    
    // default menu
    create: function()
    {
        //
        // Analyze data tab.
        //
        var tab_analysis = new mod_masthead.GalaxyMastheadTab({
            id      : "analysis",
            title   : "Analyze Data",
            content : "root/index",
            title_attribute : 'Main analysis page'
        });
        this.masthead.append(tab_analysis);

        //
        // Workflow tab.
        //

        var workflow_options = {
            id      : "workflow",
            title   : "Workflow",
            content : "workflow",
            title_attribute : 'Chain tools into workflows'
        }
        if (!this.options.user.valid){
            workflow_options.disabled = true; // disable workflows for anonymous users
            workflow_options.title_attribute = 'Please register to use workflows';
        }

        var tab_workflow = new mod_masthead.GalaxyMastheadTab(workflow_options);
        this.masthead.append(tab_workflow);

        //
        // 'Shared Items' or Libraries tab.
        //
        var tab_shared = new mod_masthead.GalaxyMastheadTab({
            id      : "shared",
            title   : "Shared Data",
            content : "library/index",
            title_attribute : 'Access public data'
        });

        tab_shared.add({
            title   : "Data Libraries",
            content : "library/index"
        });

        tab_shared.add({
            title   : "Data Libraries Beta",
            content : "library/list",
            divider : true
        });

        tab_shared.add({
            title   : "Published Histories",
            content : "history/list_published"
        });

        tab_shared.add({
            title   : "Published Workflows",
            content : "workflow/list_published"

        });

        tab_shared.add({
            title   : "Published Visualizations",
            content : "visualization/list_published"
        });

        tab_shared.add({
            title   : "Published Pages",
            content : "page/list_published"
        });

        this.masthead.append(tab_shared);

        //
        // Lab menu.
        //
        if (this.options.user.requests)
        {
            var tab_lab = new mod_masthead.GalaxyMastheadTab({
                id      : "lab",
                title   : "Lab"
            });
            tab_lab.add({
                title   : "Sequencing Requests",
                content : "requests/index"
            });
            tab_lab.add({
                title   : "Find Samples",
                content : "requests/find_samples_index"
            });
            tab_lab.add({
                title   : "Help",
                content : this.options.lims_doc_url
            });
            this.masthead.append(tab_lab);
        }

        //
        // Visualization tab.
        //
        if (this.options.user.valid)
        {
            var tab_visualization = new mod_masthead.GalaxyMastheadTab({
                id          : "visualization",
                title       : "Visualization",
                content     : "visualization/list",
                title_attribute : 'Visualize data'
            });
            tab_visualization.add({
                title       : "New Track Browser",
                content     : "visualization/trackster",
                target      : "_frame"
            });
            tab_visualization.add({
                title       : "Saved Visualizations",
                content     : "visualization/list",
                target      : "_frame"
            });
            this.masthead.append(tab_visualization);
        } else 
        {
            var tab_visualization = new mod_masthead.GalaxyMastheadTab({
                id          : "visualization",
                title       : "Visualization",
                content     : "visualization/list",
                disabled    : true,
                title_attribute : 'Please register to create visualizations'
            });
            this.masthead.append(tab_visualization);
        }

        //
        // Cloud menu.
        //
        if (this.options.enable_cloud_launch)
        {
            var tab_cloud = new mod_masthead.GalaxyMastheadTab({
                id      : "cloud",
                title   : "Cloud",
                content : "cloudlaunch/index"
            });
            tab_cloud.add({
                title   : "New Cloud Cluster",
                content : "cloudlaunch/index"
            });
            this.masthead.append(tab_cloud);
        }

        //
        // Admin.
        //
        if (this.options.is_admin_user)
        {
            var tab_admin = new mod_masthead.GalaxyMastheadTab({
                id          : "admin",
                title       : "Admin",
                content     : "admin/index",
                extra_class : "admin-only",
                title_attribute : 'Administer this Galaxy'
            });
            this.masthead.append(tab_admin);
        }

        //
        // Help tab.
        //
        var tab_help = new mod_masthead.GalaxyMastheadTab({
            id      : "help",
            title   : "Help",
            title_attribute : 'Find help with Galaxy'
        });
        if (this.options.biostar_url)
        {
            tab_help.add({
                title   : "Galaxy Q&A Site",
                content : this.options.biostar_url_redirect,
                target  : "_blank"
            });
            tab_help.add({
                title   : "Ask a question",
                content : "biostar/biostar_question_redirect",
                target  : "_blank"
            });
        }
        tab_help.add({
            title   : "Support",
            content : this.options.support_url,
            target  : "_blank"
        });
        tab_help.add({
            title   : "Search",
            content : this.options.search_url,
            target  : "_blank"
        });
        tab_help.add({
            title   : "Mailing Lists",
            content : this.options.mailing_lists,
            target  : "_blank"
        });
        tab_help.add({
            title   : "Videos",
            content : this.options.screencasts_url,
            target  : "_blank"
        });
        tab_help.add({
            title   : "Wiki",
            content : this.options.wiki_url,
            target  : "_blank"
        });
        tab_help.add({
            title   : "How to Cite Galaxy",
            content : this.options.citation_url,
            target  : "_blank"
        });
        if (!this.options.terms_url)
        {
            tab_help.add({
                title   : "Terms and Conditions",
                content : this.options.terms_url,
                target  : "_blank"
            });
        }
        this.masthead.append(tab_help);

        //
        // User tab.
        //
        if (!this.options.user.valid)
        {
            var tab_user = new mod_masthead.GalaxyMastheadTab({
                id          : "user",
                title       : "User",
                extra_class : "loggedout-only",
                title_attribute : 'Account information'
            });

            // login
            tab_user.add({
                title   : "Login",
                content : "user/login",
                target  : "galaxy_main"
            });

            // register
            if (this.options.allow_user_creation)
            {
                tab_user.add({
                    title   : "Register",
                    content : "user/create",
                    target  : "galaxy_main"
                });
            }

            // add to masthead
            this.masthead.append(tab_user);
        } else {
            var tab_user = new mod_masthead.GalaxyMastheadTab({
                id          : "user",
                title       : "User",
                extra_class : "loggedin-only",
                title_attribute : 'Account information'
            });

            // show user logged in info
            tab_user.add({
                title       : "Logged in as " + this.options.user.email
            });

            // remote user
            if (this.options.use_remote_user && this.options.remote_user_logout_href)
            {
                tab_user.add({
                    title   : "Logout",
                    content : this.options.remote_user_logout_href,
                    target  : "_top"
                });
            } else {
                tab_user.add({
                    title   : "Preferences",
                    content : "user?cntrller=user",
                    target  : "galaxy_main"
                });

                tab_user.add({
                    title   : "Custom Builds",
                    content : "user/dbkeys",
                    target  : "galaxy_main"
                });
            
                tab_user.add({
                    title   : "Logout",
                    content : "user/logout",
                    target  : "_top",
                    divider : true
                });
            }
        
            // default tabs
            tab_user.add({
                title   : "Saved Histories",
                content : "history/list",
                target  : "galaxy_main"
            });
            tab_user.add({
                title   : "Saved Datasets",
                content : "dataset/list",
                target  : "galaxy_main"
            });
            tab_user.add({
                title   : "Saved Pages",
                content : "page/list",
                target  : "_top"
            });

            tab_user.add({
                title   : "API Keys",
                content : "user/api_keys?cntrller=user",
                target  : "galaxy_main"
            });

            if (this.options.use_remote_user)
            {
                tab_user.add({
                    title   : "Public Name",
                    content : "user/edit_username?cntrller=user",
                    target  : "galaxy_main"
                });
            }

            // add to masthead
            this.masthead.append(tab_user);
        }
        
        // identify active tab
        if (this.options.active_view)
            this.masthead.highlight(this.options.active_view);
    }
});

// return
return {
    GalaxyMenu: GalaxyMenu
};

});
