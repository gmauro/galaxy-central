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

class TestRepositoryDependencyRevisions( ShedTwillTestCase ):
    '''Test dependencies on different revisions of a repository.'''
    def test_0000_initiate_users( self ):
        """Create necessary user accounts."""
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        test_user_1 = test_db_util.get_user( common.test_user_1_email )
        assert test_user_1 is not None, 'Problem retrieving user with email %s from the database' % test_user_1_email
        test_user_1_private_role = test_db_util.get_private_role( test_user_1 )
        self.logout()
        self.login( email=common.admin_email, username=common.admin_username )
        admin_user = test_db_util.get_user( common.admin_email )
        assert admin_user is not None, 'Problem retrieving user with email %s from the database' % admin_email
        admin_user_private_role = test_db_util.get_private_role( admin_user )
    def test_0005_create_category( self ):
        """Create a category for this test suite"""
        self.create_category( name='Test 0030 Repository Dependency Revisions', description='Testing repository dependencies by revision.' )
    def test_0010_create_repositories( self ):
        '''Create the emboss_5_0030, emboss_6_0030, emboss_datatypes_0030, and emboss_0030 repositories and populate the emboss_datatypes repository.'''
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        category = test_db_util.get_category_by_name( 'Test 0030 Repository Dependency Revisions' )
        emboss_5_repository = self.get_or_create_repository( name=emboss_5_repository_name, 
                                                             description=emboss_repository_description, 
                                                             long_description=emboss_repository_long_description, 
                                                             owner=common.test_user_1_name,
                                                             category_id=self.security.encode_id( category.id ) )
        emboss_6_repository = self.get_or_create_repository( name=emboss_6_repository_name, 
                                                             description=emboss_repository_description, 
                                                             long_description=emboss_repository_long_description, 
                                                             owner=common.test_user_1_name,
                                                             category_id=self.security.encode_id( category.id ) )
        datatypes_repository = self.get_or_create_repository( name=datatypes_repository_name, 
                                                              description=emboss_repository_description, 
                                                              long_description=emboss_repository_long_description, 
                                                              owner=common.test_user_1_name,
                                                              category_id=self.security.encode_id( category.id ) )
        emboss_repository = self.get_or_create_repository( name=emboss_repository_name, 
                                                           description=emboss_repository_description, 
                                                           long_description=emboss_repository_long_description, 
                                                           owner=common.test_user_1_name,
                                                           category_id=self.security.encode_id( category.id ) )
        self.upload_file( emboss_5_repository, 'emboss/emboss.tar', commit_message='Uploaded tool tarball.' )
        self.upload_file( emboss_6_repository, 'emboss/emboss.tar', commit_message='Uploaded tool tarball.' )
        self.upload_file( datatypes_repository, 'emboss/datatypes/datatypes_conf.xml', commit_message='Uploaded datatypes_conf.xml.' )
        self.upload_file( emboss_repository, 'emboss/emboss.tar', commit_message='Uploaded tool tarball.' )
    def test_0015_generate_repository_dependencies_for_emboss_5( self ):
        '''Generate a repository_dependencies.xml file specifying emboss_datatypes and upload it to the emboss_5 repository.'''
        datatypes_repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        repository_dependencies_path = self.generate_temp_path( 'test_0030', additional_paths=[ 'emboss' ] )
        self.generate_repository_dependency_xml( [ datatypes_repository ], 
                                                 self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ) )
        emboss_5_repository = test_db_util.get_repository_by_name_and_owner( emboss_5_repository_name, common.test_user_1_name )
        self.upload_file( emboss_5_repository, 
                          'repository_dependencies.xml', 
                          filepath=repository_dependencies_path, 
                          commit_message='Uploaded repository_depepndencies.xml.' )
    def test_0020_generate_repository_dependencies_for_emboss_6( self ):
        '''Generate a repository_dependencies.xml file specifying emboss_datatypes and upload it to the emboss_6 repository.'''
        emboss_6_repository = test_db_util.get_repository_by_name_and_owner( emboss_6_repository_name, common.test_user_1_name )
        repository_dependencies_path = self.generate_temp_path( 'test_0030', additional_paths=[ 'emboss' ] )
        self.upload_file( emboss_6_repository, 
                          'repository_dependencies.xml', 
                          filepath=repository_dependencies_path, 
                          commit_message='Uploaded repository_depepndencies.xml.' )
    def test_0025_generate_repository_dependency_on_emboss_5( self ):
        '''Create and upload repository_dependencies.xml for the emboss_5_0030 repository.'''
        emboss_repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        emboss_5_repository = test_db_util.get_repository_by_name_and_owner( emboss_5_repository_name, common.test_user_1_name )
        repository_dependencies_path = self.generate_temp_path( 'test_0030', additional_paths=[ 'emboss', '5' ] )
        self.generate_repository_dependency_xml( [ emboss_5_repository ], 
                                                 self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                 dependency_description='Emboss requires the Emboss 5 repository.' )
        self.upload_file( emboss_repository, 
                          'repository_dependencies.xml', 
                          filepath=repository_dependencies_path, 
                          commit_message='Uploaded dependency configuration specifying emboss_5' )
    def test_0030_generate_repository_dependency_on_emboss_6( self ):
        '''Create and upload repository_dependencies.xml for the emboss_6_0030 repository.'''
        emboss_repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        emboss_6_repository = test_db_util.get_repository_by_name_and_owner( emboss_6_repository_name, common.test_user_1_name )
        repository_dependencies_path = self.generate_temp_path( 'test_0030', additional_paths=[ 'emboss', '6' ] )
        self.generate_repository_dependency_xml( [ emboss_6_repository ], 
                                                 self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                 dependency_description='Emboss requires the Emboss 6 repository.' )
        self.upload_file( emboss_repository, 
                          'repository_dependencies.xml', 
                          filepath=repository_dependencies_path, 
                          commit_message='Uploaded dependency configuration specifying emboss_6' )
    def test_0035_verify_repository_dependency_revisions( self ):
        '''Verify that different metadata revisions of the emboss repository have different repository dependencies.'''
        repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        repository_metadata = [ ( metadata.metadata, metadata.changeset_revision ) for metadata in self.get_repository_metadata( repository ) ]
        datatypes_repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        datatypes_tip = self.get_repository_tip( datatypes_repository )
        # Iterate through all metadata revisions and check for repository dependencies.
        for metadata, changeset_revision in repository_metadata:
            strings_displayed = [ str( metadata_elem ) for metadata_elem in metadata[ 'repository_dependencies' ][ 'repository_dependencies' ][ 0 ] ]
            # Remove the tool shed URL, because that's not displayed on the page (yet?)
            strings_displayed.pop( strings_displayed.index( self.url ) )
            # Add the dependency description and datatypes repository details to the strings to check.
            strings_displayed.extend( [ metadata[ 'repository_dependencies' ][ 'description' ], 
                                      datatypes_repository_name, 
                                      datatypes_repository.user.username, 
                                      datatypes_tip ] )
            strings_displayed.extend( [ 'Tool dependencies', 'emboss', '5.0.0', 'package' ] )
            self.display_manage_repository_page( repository, 
                                                 changeset_revision=changeset_revision, 
                                                 strings_displayed=strings_displayed )
    def test_0040_verify_repository_metadata( self ):
        '''Verify that resetting the metadata does not change it.'''
        emboss_repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        emboss_5_repository = test_db_util.get_repository_by_name_and_owner( emboss_5_repository_name, common.test_user_1_name )
        emboss_6_repository = test_db_util.get_repository_by_name_and_owner( emboss_6_repository_name, common.test_user_1_name )
        datatypes_repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        for repository in [ emboss_repository, emboss_5_repository, emboss_6_repository, datatypes_repository ]:
            self.verify_unchanged_repository_metadata( repository )
