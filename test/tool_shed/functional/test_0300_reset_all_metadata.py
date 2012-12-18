from tool_shed.base.twilltestcase import ShedTwillTestCase, common, os
import tool_shed.base.test_db_util as test_db_util

datatypes_repository_name = 'emboss_datatypes_0020'
datatypes_repository_description = "Galaxy applicable data formats used by Emboss tools."
datatypes_repository_long_description = "Galaxy applicable data formats used by Emboss tools.  This repository contains no tools."
emboss_repository_description = 'Galaxy wrappers for Emboss version 5.0.0 tools'
emboss_repository_long_description = 'Galaxy wrappers for Emboss version 5.0.0 tools'
workflow_filename = 'Workflow_for_0060_filter_workflow_repository.ga'
workflow_name = 'Workflow for 0060_filter_workflow_repository'

class TestResetAllRepositoryMetadata( ShedTwillTestCase ):
    '''Verify that the "Reset selected metadata" feature works.'''
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
    def test_0005_create_repositories_and_categories( self ):
        category_0000 = self.create_category( name='Test 0000 Basic Repository Features 1', description='Test 0000 Basic Repository Features 1' )
        category_0001 = self.create_category( name='Test 0000 Basic Repository Features 2', description='Test 0000 Basic Repository Features 2' )
        category_0010 = self.create_category( name='Test 0010 Repository With Tool Dependencies', description='Tests for a repository with tool dependencies.' )
        category_0020 = self.create_category( name='Test 0020 Basic Repository Dependencies', description='Testing basic repository dependency features.' )
        category_0030 = self.create_category( name='Test 0030 Repository Dependency Revisions', description='Testing repository dependencies by revision.' )
        category_0040 = self.create_category( name='test_0040_repository_circular_dependencies', description='Testing handling of circular repository dependencies.' )
        category_0050 = self.create_category( name='test_0050_repository_n_level_circular_dependencies', description='Testing handling of circular repository dependencies to n levels.' )
        category_0060 = self.create_category( name='Test 0060 Workflow Features', description='Test 0060 - Workflow Features' )
        self.logout()
        self.login( email=common.test_user_1_email, username=common.test_user_1_name )
        repository = self.get_or_create_repository( name='filtering_0000', 
                                                    description="Galaxy's filtering tool", 
                                                    long_description="Long description of Galaxy's filtering tool", 
                                                    owner=common.test_user_1_name,
                                                    category_id=self.security.encode_id( category_0000.id ) )
        if self.repository_is_new( repository ):
            self.upload_file( repository, 'filtering/filtering_1.1.0.tar', commit_message="Uploaded filtering 1.1.0" )
            self.upload_file( repository, 'filtering/filtering_2.2.0.tar', commit_message="Uploaded filtering 2.2.0" )
        repository = self.get_or_create_repository( name='freebayes_0010', 
                                                    description="Galaxy's freebayes tool", 
                                                    long_description="Long description of Galaxy's freebayes tool", 
                                                    owner=common.test_user_1_name,
                                                    category_id=self.security.encode_id( category_0000.id ),
                                                    strings_displayed=[] )
        if self.repository_is_new( repository ):
            self.upload_file( repository, 'freebayes/freebayes.xml', valid_tools_only=False, commit_message='Uploaded.', strings_displayed=[] )
            self.upload_file( repository, 'freebayes/tool_data_table_conf.xml.sample', valid_tools_only=False, commit_message='Uploaded.', strings_displayed=[] )
            self.upload_file( repository, 'freebayes/sam_fa_indices.loc.sample', valid_tools_only=False, commit_message='Uploaded.', strings_displayed=[] )
            self.upload_file( repository, 'freebayes/tool_dependencies.xml', commit_message='Uploaded.' )
        repository = self.get_or_create_repository( name='emboss_datatypes_0020', 
                                                    description="Galaxy applicable data formats used by Emboss tools.", 
                                                    long_description="Galaxy applicable data formats used by Emboss tools. This repository contains no tools.", 
                                                    owner=common.test_user_1_name,
                                                    category_id=self.security.encode_id( category_0010.id ),
                                                    strings_displayed=[] )
        if self.repository_is_new( repository ):
            self.upload_file( repository, 'emboss/datatypes/datatypes_conf.xml', commit_message='Uploaded datatypes_conf.xml.' )
            repository = self.get_or_create_repository( name='emboss_0020', 
                                                 description='Galaxy wrappers for Emboss version 5.0.0 tools', 
                                                 long_description='Galaxy wrappers for Emboss version 5.0.0 tools', 
                                                 owner=common.test_user_1_name,
                                                 category_id=self.security.encode_id( category_0020.id ),
                                                 strings_displayed=[] )
            self.upload_file( repository, 'emboss/emboss.tar', commit_message='Uploaded emboss_5.tar' )
        datatypes_repository = self.get_or_create_repository( name='emboss_datatypes_0030', 
                                                              description=datatypes_repository_description, 
                                                              long_description=datatypes_repository_long_description, 
                                                              owner=common.test_user_1_name,
                                                              category_id=self.security.encode_id( category_0030.id ), 
                                                              strings_displayed=[] )
        if self.repository_is_new( datatypes_repository ):
            self.upload_file( datatypes_repository, 'emboss/datatypes/datatypes_conf.xml', commit_message='Uploaded datatypes_conf.xml.' )
            emboss_5_repository = self.get_or_create_repository( name='emboss_5_0030', 
                                                                 description=emboss_repository_description, 
                                                                 long_description=emboss_repository_long_description, 
                                                                 owner=common.test_user_1_name,
                                                                 category_id=self.security.encode_id( category_0030.id ), 
                                                                 strings_displayed=[] )
            self.upload_file( emboss_5_repository, 'emboss/emboss.tar', commit_message='Uploaded emboss.tar' )
            repository_dependencies_path = self.generate_temp_path( 'test_0330', additional_paths=[ 'emboss', '5' ] )
            self.generate_repository_dependency_xml( [ datatypes_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ) )
            self.upload_file( emboss_5_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded repository_dependencies.xml' )
            emboss_6_repository = self.get_or_create_repository( name='emboss_6_0030', 
                                                                 description=emboss_repository_description, 
                                                                 long_description=emboss_repository_long_description, 
                                                                 owner=common.test_user_1_name,
                                                                 category_id=self.security.encode_id( category_0030.id ), 
                                                                 strings_displayed=[] )
            self.upload_file( emboss_6_repository, 'emboss/emboss.tar', commit_message='Uploaded emboss.tar' )
            repository_dependencies_path = self.generate_temp_path( 'test_0330', additional_paths=[ 'emboss', '6' ] )
            self.generate_repository_dependency_xml( [ datatypes_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ) )
            self.upload_file( emboss_6_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded repository_dependencies.xml' )
            emboss_repository = self.get_or_create_repository( name='emboss_0030', 
                                                               description=emboss_repository_description, 
                                                               long_description=emboss_repository_long_description, 
                                                               owner=common.test_user_1_name,
                                                               category_id=self.security.encode_id( category_0030.id ), 
                                                               strings_displayed=[] )
            self.upload_file( emboss_repository, 'emboss/emboss.tar', commit_message='Uploaded emboss.tar' )
            repository_dependencies_path = self.generate_temp_path( 'test_0330', additional_paths=[ 'emboss', '5' ] )
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
        repository = self.get_or_create_repository( name='freebayes_0040', 
                                                    description="Galaxy's freebayes tool", 
                                                    long_description="Long description of Galaxy's freebayes tool", 
                                                    owner=common.test_user_1_name,
                                                    category_id=self.security.encode_id( category_0040.id ),
                                                    strings_displayed=[] )
        if self.repository_is_new( repository ):
            self.upload_file( repository, 'freebayes/freebayes.tar', commit_message='Uploaded freebayes.tar.' )
            repository = self.get_or_create_repository( name='filtering_0040', 
                                                        description="Galaxy's filtering tool", 
                                                        long_description="Long description of Galaxy's filtering tool", 
                                                        owner=common.test_user_1_name,
                                                        category_id=self.security.encode_id( category_0040.id ),
                                                        strings_displayed=[] )
            self.upload_file( repository, 'filtering/filtering_1.1.0.tar', commit_message='Uploaded filtering.tar.' )
            freebayes_repository = test_db_util.get_repository_by_name_and_owner( 'freebayes_0040', common.test_user_1_name )
            filtering_repository = test_db_util.get_repository_by_name_and_owner( 'filtering_0040', common.test_user_1_name )
            repository_dependencies_path = self.generate_temp_path( 'test_0340', additional_paths=[ 'dependencies' ] )
            self.generate_repository_dependency_xml( [ freebayes_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                     dependency_description='Filtering 1.1.0 depends on the freebayes repository.' )
            self.upload_file( filtering_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded dependency on freebayes' )
            self.generate_repository_dependency_xml( [ filtering_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                     dependency_description='Freebayes depends on the filtering repository.' )
            self.upload_file( freebayes_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded dependency on filtering' )
        datatypes_repository = self.get_or_create_repository( name='emboss_datatypes_0050', 
                                                    description="Datatypes for emboss", 
                                                    long_description="Long description of Emboss' datatypes", 
                                                    owner=common.test_user_1_name,
                                                    category_id=self.security.encode_id( category_0050.id ),
                                                    strings_displayed=[] )
        if self.repository_is_new( datatypes_repository ):
            emboss_repository = self.get_or_create_repository( name='emboss_0050', 
                                                        description="Galaxy's emboss tool", 
                                                        long_description="Long description of Galaxy's emboss tool", 
                                                        owner=common.test_user_1_name,
                                                        category_id=self.security.encode_id( category_0050.id ),
                                                        strings_displayed=[] )
            filtering_repository = self.get_or_create_repository( name='filtering_0050', 
                                                                  description="Galaxy's filtering tool", 
                                                                  long_description="Long description of Galaxy's filtering tool", 
                                                                  owner=common.test_user_1_name,
                                                                  category_id=self.security.encode_id( category_0050.id ),
                                                                  strings_displayed=[] )
            freebayes_repository = self.get_or_create_repository( name='freebayes_0050', 
                                                                  description="Galaxy's freebayes tool", 
                                                                  long_description="Long description of Galaxy's freebayes tool", 
                                                                  owner=common.test_user_1_name,
                                                                  category_id=self.security.encode_id( category_0050.id ),
                                                                  strings_displayed=[] )
            self.upload_file( datatypes_repository, 'emboss/datatypes/datatypes_conf.xml', commit_message='Uploaded datatypes_conf.xml.' )
            self.upload_file( emboss_repository, 'emboss/emboss.tar', commit_message='Uploaded tool tarball.' )
            self.upload_file( freebayes_repository, 'freebayes/freebayes.tar', commit_message='Uploaded freebayes.tar.' )
            self.upload_file( filtering_repository, 'filtering/filtering_1.1.0.tar', commit_message='Uploaded filtering.tar.' )
            repository_dependencies_path = self.generate_temp_path( 'test_0350', additional_paths=[ 'emboss' ] )
            self.generate_repository_dependency_xml( [ datatypes_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                     dependency_description='Emboss depends on the emboss_datatypes repository.' )
            self.upload_file( emboss_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded dependency on emboss_datatypes.' )
            repository_dependencies_path = self.generate_temp_path( 'test_0350', additional_paths=[ 'filtering' ] )
            self.generate_repository_dependency_xml( [ emboss_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                     dependency_description='Filtering depends on the emboss repository.' )
            self.upload_file( filtering_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded dependency on emboss.' )
            repository_dependencies_path = self.generate_temp_path( 'test_0350', additional_paths=[ 'freebayes' ] )
            self.generate_repository_dependency_xml( [ filtering_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                     dependency_description='Emboss depends on the filtering repository.' )
            self.upload_file( emboss_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded dependency on filtering.' )
            self.generate_repository_dependency_xml( [ datatypes_repository, emboss_repository, filtering_repository, freebayes_repository ], 
                                                     self.get_filename( 'repository_dependencies.xml', filepath=repository_dependencies_path ), 
                                                     dependency_description='Freebayes depends on the filtering repository.' )
            self.upload_file( freebayes_repository, 
                              'repository_dependencies.xml', 
                              filepath=repository_dependencies_path, 
                              commit_message='Uploaded dependency on filtering.' )
        workflow_repository = self.get_or_create_repository( name='filtering_0060', 
                                                             description="Galaxy's filtering tool", 
                                                             long_description="Long description of Galaxy's filtering tool", 
                                                             owner=common.test_user_1_name,
                                                             category_id=self.security.encode_id( category_0060.id ),
                                                             strings_displayed=[] )
        if self.repository_is_new( workflow_repository ):
            workflow = file( self.get_filename( 'filtering_workflow/Workflow_for_0060_filter_workflow_repository.ga' ), 'r' ).read()
            workflow = workflow.replace(  '__TEST_TOOL_SHED_URL__', self.url.replace( 'http://', '' ) )
            workflow_filepath = self.generate_temp_path( 'test_0360', additional_paths=[ 'filtering_workflow' ] )
            os.makedirs( workflow_filepath )
            file( os.path.join( workflow_filepath, workflow_filename ), 'w+' ).write( workflow )
            self.upload_file( workflow_repository, 
                              workflow_filename, 
                              filepath=workflow_filepath, 
                              commit_message='Uploaded filtering workflow.' )
            self.upload_file( workflow_repository, 
                              'filtering/filtering_2.2.0.tar', 
                              commit_message='Uploaded filtering tool.' )
    def test_0010_reset_metadata_on_all_repositories( self ):
        '''Reset metadata on all repositories, then verify that it has not changed.'''
        self.logout()
        self.login( email=common.admin_email, username=common.admin_username )
        old_metadata = dict()
        new_metadata = dict()
        repositories = test_db_util.get_all_repositories()
        for repository in repositories:
            old_metadata[ self.security.encode_id( repository.id ) ] = dict()
            for metadata in self.get_repository_metadata( repository ):
                old_metadata[ self.security.encode_id( repository.id ) ][ metadata.changeset_revision ] = metadata.metadata 
        self.reset_metadata_on_selected_repositories( old_metadata.keys() )
        for repository in repositories:
            new_metadata[ self.security.encode_id( repository.id ) ] = dict()
            for metadata in self.get_repository_metadata( repository ):
                new_metadata[ self.security.encode_id( repository.id ) ][ metadata.changeset_revision ] = metadata.metadata 
            if old_metadata[ self.security.encode_id( repository.id ) ] != new_metadata[ self.security.encode_id( repository.id ) ]:
                raise AssertionError( 'Metadata changed after reset for repository %s.' % repository.name )
