from tool_shed.base.twilltestcase import ShedTwillTestCase, common, os
import tool_shed.base.test_db_util as test_db_util

repository_name = 'bismark_0070'
repository_description = "Galaxy's bismark wrapper"
repository_long_description = "Long description of Galaxy's bismark wrapper"
category_name = 'Test 0070 Invalid Tool Revisions'

class TestBismarkRepository( ShedTwillTestCase ):
    '''Testing bismark with valid and invalid tool entries.'''
    def test_0000_create_or_login_admin_user( self ):
        """Create necessary user accounts and login as an admin user."""
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
    def test_0005_create_category_and_repository( self ):
        """Create a category for this test suite, then create and populate a bismark repository. It should contain at least one each valid and invalid tool."""
        category = self.create_category( name=category_name, description='Tests for a repository with invalid tool revisions.' )
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        repository = self.get_or_create_repository( name=repository_name, 
                                                    description=repository_description, 
                                                    long_description=repository_long_description, 
                                                    owner=common.test_user_1_name,
                                                    category_id=self.security.encode_id( category.id ), 
                                                    strings_displayed=[] )
        self.upload_file( repository, 
                          'bismark/bismark.tar', 
                          valid_tools_only=False,
                          strings_displayed=[],
                          commit_message='Uploaded the tool tarball.' )
        self.display_manage_repository_page( repository, strings_displayed=[ 'Invalid tools' ] )
        invalid_revision = self.get_repository_tip( repository )
        self.upload_file( repository, 
                          'bismark/bismark_methylation_extractor.xml', 
                          valid_tools_only=False, 
                          strings_displayed=[],
                          remove_repo_files_not_in_tar='No',
                          commit_message='Uploaded an updated tool xml.' )
        valid_revision = self.get_repository_tip( repository )
        test_db_util.refresh( repository )
        self.check_repository_tools_for_changeset_revision( repository, valid_revision )
        self.check_repository_invalid_tools_for_changeset_revision( repository, invalid_revision )
