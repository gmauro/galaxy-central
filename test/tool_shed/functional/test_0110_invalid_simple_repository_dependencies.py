from tool_shed.base.twilltestcase import ShedTwillTestCase, common, os
import tool_shed.base.test_db_util as test_db_util

datatypes_repository_name = 'emboss_datatypes_0110'
datatypes_repository_description = "Galaxy applicable data formats used by Emboss tools."
datatypes_repository_long_description = "Galaxy applicable data formats used by Emboss tools.  This repository contains no tools."

emboss_repository_name = 'emboss_0110'
emboss_repository_description = 'Galaxy wrappers for Emboss version 5.0.0 tools'
emboss_repository_long_description = 'Galaxy wrappers for Emboss version 5.0.0 tools'

category_name = 'Test 0110 Invalid Repository Dependencies'
category_desc = 'Test 0110 Invalid Repository Dependencies'

class TestBasicRepositoryDependencies( ShedTwillTestCase ):
    '''Testing emboss 5 with repository dependencies.'''
    def test_0000_initiate_users( self ):
        """Create necessary user accounts and login as an admin user."""
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        test_user_1 = test_db_util.get_user( common.test_user_1_email )
        assert test_user_1 is not None, 'Problem retrieving user with email %s from the database' % common.test_user_1_email
        test_user_1_private_role = test_db_util.get_private_role( test_user_1 )
        self.logout()
        self.login( email=common.admin_email, username=common.admin_username )
        admin_user = test_db_util.get_user( common.admin_email )
        assert admin_user is not None, 'Problem retrieving user with email %s from the database' % common.admin_email
        admin_user_private_role = test_db_util.get_private_role( admin_user )
    def test_0005_create_category( self ):
        """Create a category for this test suite"""
        self.create_category( name=category_name, description=category_desc )
    def test_0010_create_emboss_datatypes_repository_and_upload_tarball( self ):
        '''Create and populate the emboss_datatypes repository.'''
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        category = test_db_util.get_category_by_name( category_name )
        repository = self.get_or_create_repository( name=datatypes_repository_name, 
                                             description=datatypes_repository_description, 
                                             long_description=datatypes_repository_long_description, 
                                             owner=common.test_user_1_name,
                                             category_id=self.security.encode_id( category.id ), 
                                             strings_displayed=[] )
        self.upload_file( repository, 'emboss/datatypes/datatypes_conf.xml', commit_message='Uploaded datatypes_conf.xml.' )
    def test_0015_verify_datatypes_in_datatypes_repository( self ):
        '''Verify that the emboss_datatypes repository contains datatype entries.'''
        repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        self.display_manage_repository_page( repository, strings_displayed=[ 'Datatypes', 'equicktandem', 'hennig86', 'vectorstrip' ] )
    def test_0020_create_emboss_5_repository_and_upload_files( self ):
        '''Create and populate the emboss_5_0110 repository.'''
        category = test_db_util.get_category_by_name( category_name )
        repository = self.get_or_create_repository( name=emboss_repository_name, 
                                             description=emboss_repository_description, 
                                             long_description=emboss_repository_long_description, 
                                             owner=common.test_user_1_name,
                                             category_id=self.security.encode_id( category.id ), 
                                             strings_displayed=[] )
        self.upload_file( repository, 'emboss/emboss.tar', commit_message='Uploaded emboss_5.tar' )
    def test_0025_generate_repository_dependency_with_invalid_url( self ):
        '''Generate a repository dependency for emboss 5 with an invalid URL.'''
        dependency_path = self.generate_temp_path( 'test_0110', additional_paths=[ 'simple' ] )
        xml_filename = self.get_filename( 'repository_dependencies.xml', filepath=dependency_path )
        repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        emboss_repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        url = 'http://http://this is not an url!'
        name = repository.name
        owner = repository.user.username
        changeset_revision = self.get_repository_tip( repository )
        self.generate_invalid_dependency_xml( xml_filename, url, name, owner, changeset_revision, complex=False, description='This is invalid.' )
        strings_displayed = [ 'Invalid tool shed <b>%s</b> defined for repository <b>%s</b>' % ( url, repository.name ) ] 
        self.upload_file( emboss_repository, 
                          'repository_dependencies.xml',
                          valid_tools_only=False,
                          filepath=dependency_path, 
                          commit_message='Uploaded dependency on emboss_datatypes_0110 with invalid url.',
                          strings_displayed=strings_displayed )
    def test_0030_generate_repository_dependency_with_invalid_name( self ):
        '''Generate a repository dependency for emboss 5 with an invalid name.'''
        dependency_path = self.generate_temp_path( 'test_0110', additional_paths=[ 'simple' ] )
        xml_filename = self.get_filename( 'repository_dependencies.xml', filepath=dependency_path )
        repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        emboss_repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        url = self.url
        name = '!?invalid?!'
        owner = repository.user.username
        changeset_revision = self.get_repository_tip( repository )
        self.generate_invalid_dependency_xml( xml_filename, url, name, owner, changeset_revision, complex=False, description='This is invalid.' )
        strings_displayed = [ 'Invalid repository name <b>%s</b> defined.' % name ] 
        self.upload_file( emboss_repository, 
                          'repository_dependencies.xml',
                          valid_tools_only=False,
                          filepath=dependency_path, 
                          commit_message='Uploaded dependency on emboss_datatypes_0110 with invalid url.',
                          strings_displayed=strings_displayed )
    def test_0035_generate_repository_dependency_with_invalid_owner( self ):
        '''Generate a repository dependency for emboss 5 with an invalid owner.'''
        dependency_path = self.generate_temp_path( 'test_0110', additional_paths=[ 'simple' ] )
        xml_filename = self.get_filename( 'repository_dependencies.xml', filepath=dependency_path )
        repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        emboss_repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        url = self.url
        name = repository.name
        owner = '!?invalid?!'
        changeset_revision = self.get_repository_tip( repository )
        self.generate_invalid_dependency_xml( xml_filename, url, name, owner, changeset_revision, complex=False, description='This is invalid.' )
        strings_displayed = [ 'Invalid owner <b>%s</b> defined for repository <b>%s</b>' % ( owner, repository.name ) ] 
        self.upload_file( emboss_repository, 
                          'repository_dependencies.xml',
                          valid_tools_only=False,
                          filepath=dependency_path, 
                          commit_message='Uploaded dependency on emboss_datatypes_0110 with invalid url.',
                          strings_displayed=strings_displayed )
    def test_0040_generate_repository_dependency_with_invalid_changeset_revision( self ):
        '''Generate a repository dependency for emboss 5 with an invalid changeset revision.'''
        dependency_path = self.generate_temp_path( 'test_0110', additional_paths=[ 'simple', 'invalid' ] )
        xml_filename = self.get_filename( 'repository_dependencies.xml', filepath=dependency_path )
        repository = test_db_util.get_repository_by_name_and_owner( datatypes_repository_name, common.test_user_1_name )
        emboss_repository = test_db_util.get_repository_by_name_and_owner( emboss_repository_name, common.test_user_1_name )
        url = self.url
        name = repository.name
        owner = repository.user.username
        changeset_revision = '!?invalid?!'
        self.generate_invalid_dependency_xml( xml_filename, url, name, owner, changeset_revision, complex=False, description='This is invalid.' )
        strings_displayed = [ 'Invalid changeset revision <b>%s</b> defined.' % changeset_revision ] 
        self.upload_file( emboss_repository, 
                          'repository_dependencies.xml',
                          valid_tools_only=False,
                          filepath=dependency_path, 
                          commit_message='Uploaded dependency on emboss_datatypes_0110 with invalid url.',
                          strings_displayed=strings_displayed )
