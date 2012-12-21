from tool_shed.base.twilltestcase import ShedTwillTestCase, common, os
import tool_shed.base.test_db_util as test_db_util

datatypes_repository_name = 'emboss_datatypes_0030'
datatypes_repository_description = "Galaxy applicable data formats used by Emboss tools."
datatypes_repository_long_description = "Galaxy applicable data formats used by Emboss tools.  This repository contains no tools."

emboss_repository_name = 'emboss_0030'
emboss_5_repository_name = 'emboss_5_0030'
emboss_6_repository_name = 'emboss_6_0030'
emboss_repository_description = 'Galaxy wrappers for Emboss version 5.0.0 tools'
emboss_repository_long_description = 'Galaxy wrappers for Emboss version 5.0.0 tools'

class UninstallingAndReinstallingRepositories( ShedTwillTestCase ):
    '''Test uninstalling and reinstalling a repository with repository dependency revisions.'''
    def test_0000_initiate_users( self ):
        """Create necessary user accounts."""
        self.galaxy_logout()
        self.galaxy_login( email=common.admin_email, username=common.admin_username )
        admin_user = test_db_util.get_galaxy_user( common.admin_email )
        assert admin_user is not None, 'Problem retrieving user with email %s from the database' % admin_email
        admin_user_private_role = test_db_util.get_galaxy_private_role( admin_user )
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        test_user_1 = test_db_util.get_user( common.test_user_1_email )
        assert test_user_1 is not None, 'Problem retrieving user with email %s from the database' % test_user_1_email
        test_user_1_private_role = test_db_util.get_private_role( test_user_1 )
        self.logout()
        self.login( email=common.admin_email, username=common.admin_username )
        admin_user = test_db_util.get_user( common.admin_email )
        assert admin_user is not None, 'Problem retrieving user with email %s from the database' % common.admin_email
        admin_user_private_role = test_db_util.get_private_role( admin_user )
    def test_0005_ensure_repositories_and_categories_exist( self ):
        '''Create the 0030 category and upload the emboss repository to the tool shed, if necessary.'''
        category = self.create_category( name='Test 0030 Repository Dependency Revisions', description='Tests for a repository with tool dependencies.' )
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        datatypes_repository = self.get_or_create_repository( name=datatypes_repository_name, 
                                                              description=datatypes_repository_description, 
                                                              long_description=datatypes_repository_long_description, 
                                                              owner=common.test_user_1_name,
                                                              category_id=self.security.encode_id( category.id ), 
                                                              strings_displayed=[] )
        if self.repository_is_new( datatypes_repository ):
            self.upload_file( datatypes_repository, 'emboss/datatypes/datatypes_conf.xml', commit_message='Uploaded datatypes_conf.xml.' )
            emboss_5_repository = self.get_or_create_repository( name=emboss_5_repository_name, 
                                                                 description=emboss_repository_description, 
                                                                 long_description=emboss_repository_long_description, 
                                                                 owner=common.test_user_1_name,
                                                                 category_id=self.security.encode_id( category.id ), 
                                                                 strings_displayed=[] )
            self.upload_file( emboss_5_repository, 'emboss/emboss.tar', commit_message='Uploaded emboss.tar' )
            repository_dependencies_path = self.generate_temp_path( 'test_1030', additional_paths=[ 'emboss', '5' ] )
            self.generate_repository_dependency_xml( [ datatypes_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ) )
            self.upload_file( emboss_5_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded repository_dependencies.xml' )
            emboss_6_repository = self.get_or_create_repository( name=emboss_6_repository_name, 
                                                                 description=emboss_repository_description, 
                                                                 long_description=emboss_repository_long_description, 
                                                                 owner=common.test_user_1_name,
                                                                 category_id=self.security.encode_id( category.id ), 
                                                                 strings_displayed=[] )
            self.upload_file( emboss_6_repository, 'emboss/emboss.tar', commit_message='Uploaded emboss.tar' )
            repository_dependencies_path = self.generate_temp_path( 'test_1030', additional_paths=[ 'emboss', '6' ] )
            self.generate_repository_dependency_xml( [ datatypes_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ) )
            self.upload_file( emboss_6_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded repository_dependencies.xml' )
            emboss_repository = self.get_or_create_repository( name=emboss_repository_name, 
                                                               description=emboss_repository_description, 
                                                               long_description=emboss_repository_long_description, 
                                                               owner=common.test_user_1_name,
                                                               category_id=self.security.encode_id( category.id ), 
                                                               strings_displayed=[] )
            self.upload_file( emboss_repository, 'emboss/emboss.tar', commit_message='Uploaded emboss.tar' )
            repository_dependencies_path = self.generate_temp_path( 'test_1030', additional_paths=[ 'emboss', '5' ] )
            self.generate_repository_dependency_xml( [ emboss_5_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ) )
            self.upload_file( emboss_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded repository_dependencies.xml' )
            self.generate_repository_dependency_xml( [ emboss_6_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ) )
            self.upload_file( emboss_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded repository_dependencies.xml' )
    def test_0010_install_emboss_repository( self ):
        '''Install the emboss repository into the Galaxy instance.'''
        self.galaxy_logout()
        self.galaxy_login( email=common.admin_email, username=common.admin_username )
        self.install_repository( emboss_repository_name, 
                                 common.test_user_1_name, 
                                 'Test 0030 Repository Dependency Revisions', 
                                 new_tool_panel_section='test_1210' )
        installed_repository = test_db_util.get_installed_repository_by_name_owner( emboss_repository_name, common.test_user_1_name )
        strings_displayed = [ installed_repository.name,
                              installed_repository.description,
                              installed_repository.owner, 
                              installed_repository.tool_shed, 
                              installed_repository.installed_changeset_revision ]
        self.display_galaxy_browse_repositories_page( strings_displayed=strings_displayed )
    def test_0015_uninstall_emboss_repository( self ):
        '''Uninstall the emboss repository.'''
        installed_repository = test_db_util.get_installed_repository_by_name_owner( emboss_repository_name, common.test_user_1_name )
        self.uninstall_repository( installed_repository, remove_from_disk=True )
        strings_not_displayed = [ installed_repository.installed_changeset_revision ]
        self.display_galaxy_browse_repositories_page( strings_not_displayed=strings_not_displayed )
    def test_0020_reinstall_emboss_repository( self ):
        '''Reinstall the emboss repository.'''
        installed_repository = test_db_util.get_installed_repository_by_name_owner( emboss_repository_name, common.test_user_1_name )
        self.reinstall_repository( installed_repository )
        strings_displayed = [ installed_repository.name,
                              installed_repository.description,
                              installed_repository.owner, 
                              installed_repository.tool_shed, 
                              installed_repository.installed_changeset_revision ]
        self.display_galaxy_browse_repositories_page( strings_displayed=strings_displayed )
        self.display_installed_repository_manage_page( installed_repository, 
                                                       strings_displayed=[ 'Installed tool shed repository', 'Valid tools', 'emboss' ] )
        self.verify_tool_metadata_for_installed_repository( installed_repository )
    def test_0025_deactivate_emboss_repository( self ):
        '''Deactivate the emboss repository without removing it from disk.'''
        installed_repository = test_db_util.get_installed_repository_by_name_owner( emboss_repository_name, common.test_user_1_name )
        self.uninstall_repository( installed_repository, remove_from_disk=False )
        strings_not_displayed = [ installed_repository.installed_changeset_revision ]
        self.display_galaxy_browse_repositories_page( strings_not_displayed=strings_not_displayed )
    def test_0030_reactivate_emboss_repository( self ):
        '''Reactivate the emboss repository and verify that it now shows up in the list of installed repositories.'''
        installed_repository = test_db_util.get_installed_repository_by_name_owner( emboss_repository_name, common.test_user_1_name )
        self.reactivate_repository( installed_repository )
        strings_displayed = [ installed_repository.name,
                              installed_repository.description,
                              installed_repository.owner, 
                              installed_repository.tool_shed, 
                              installed_repository.installed_changeset_revision ]
        self.display_galaxy_browse_repositories_page( strings_displayed=strings_displayed )
        self.display_installed_repository_manage_page( installed_repository, 
                                                       strings_displayed=[ 'Installed tool shed repository', 'Valid tools', 'emboss' ] )
        self.verify_tool_metadata_for_installed_repository( installed_repository )
