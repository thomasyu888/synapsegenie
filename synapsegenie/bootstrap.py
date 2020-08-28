"""Bootstrap the components of a project to be used with the GENIE framework.
"""
import random
import tempfile

import synapseclient
import pandas

from . import config


def main(syn):
    # Determine which file formats are going to be used.
    format_registry = config.collect_format_types(['example_registry'])

    # Basic setup of the project
    project_name = "Testing Synapse Genie"

    # Determine the short and long names of the centers.
    center_abbreviations = ['AAA', 'BBB', 'CCC']
    center_names = center_abbreviations

    # Create the project
    project = synapseclient.Project(project_name)
    project = syn.store(project)

    # Create a folder for log files generated by the GENIE processes
    # of validation and updating the database tables
    logs_folder = synapseclient.Folder(name='Logs', parent=project)
    logs_folder = syn.store(logs_folder)

    # Folder for individual center folders
    root_center_folder = synapseclient.Folder(name='Centers', parent=project)
    root_center_folder = syn.store(root_center_folder)

    # The folders for each center where they will upload files for validation
    # and submission. There is one folder per center.
    # This currently deviates from the original GENIE setup of having an
    # 'Input' and 'Staging' folder for each center.
    center_folders = [
        synapseclient.Folder(name=name, parent=root_center_folder)
        for name in center_abbreviations
    ]
    center_folders = [syn.store(folder) for folder in center_folders]

    # Make some fake data that only contains basic text to check
    # for validation.

    n_files = 5 # number of files per center to create

    for folder in center_folders:
        for idx in range(n_files):
            tmp = tempfile.NamedTemporaryFile(prefix=f'TEST-{folder.name}',
                                              suffix='.txt')
            with open(tmp.name, mode='w') as fh:
                fh.write(random.choice(['ERROR', 'VALID', 'NOPE']))
            synfile = syn.store(synapseclient.File(tmp.name, parent=folder))

    # Set up the table that holds the validation status of all submitted files.
    status_table_col_defs = [
        {'name': 'id',
         'columnType': 'ENTITYID'},
        {'name': 'md5',
         'columnType': 'STRING',
         'maximumSize': 1000},
        {'name': 'status',
         'columnType': 'STRING',
         'maximumSize': 50,
         'facetType': 'enumeration'},
        {'name': 'name',
         'columnType': 'STRING',
         'maximumSize': 1000},
        {'name': 'center',
         'columnType': 'STRING',
         'maximumSize': 20,
         'facetType': 'enumeration'},
        {'name': 'modifiedOn',
         'columnType': 'DATE'},
        {'name': 'versionNumber',
         'columnType': 'STRING',
         'maximumSize': 50},
        {'name': 'fileType',
         'columnType': 'STRING',
         'maximumSize': 50}
    ]

    status_table_cols = [synapseclient.Column(**col)
                         for col in status_table_col_defs]

    status_schema = synapseclient.Schema(name='Status Table',
                                         columns=status_table_cols,
                                         parent=project)
    status_schema = syn.store(status_schema)

    # Set up the table that maps the center abbreviation to the folder where
    # their data is uploaded. This is used by the GENIE framework to find the
    # files to validate for a center.
    center_map_table_defs = [
        {'name': 'name',
         'columnType': 'STRING',
         'maximumSize': 250},
        {'name': 'center',
         'columnType': 'STRING',
         'maximumSize': 50},
        {'name': 'inputSynId',
         'columnType': 'ENTITYID'},
        # {'name': 'stagingSynId',
        #  'columnType': 'ENTITYID'},
        {'name': 'release',
         'defaultValue': 'false',
         'columnType': 'BOOLEAN'}
        # {'id': '68438',
        #  'name': 'mutationInCisFilter',
        #  'defaultValue': 'true',
        #  'columnType': 'BOOLEAN',
        #  'concreteType': 'org.sagebionetworks.repo.model.table.ColumnModel'}
    ]

    center_map_cols = [synapseclient.Column(**col)
                       for col in center_map_table_defs]

    center_schema = synapseclient.Schema(name='Center Table',
                                         columns=center_map_cols,
                                         parent=project)
    center_schema = syn.store(center_schema)

    # Add the center folders created above to this table.
    center_folder_ids = [folder.id for folder in center_folders]
    center_df = pandas.DataFrame(dict(name=center_names,
                                      center=center_abbreviations, 
                                      inputSynId=center_folder_ids))

    tbl = synapseclient.Table(schema=center_schema, values=center_df)
    tbl = syn.store(tbl)

    # Create a table that stores the error logs for each submitted file.
    error_col_defs = [
        {'name': 'id',
         'columnType': 'ENTITYID'},
        {'name': 'center',
         'columnType': 'STRING',
         'maximumSize': 50,
         'facetType': 'enumeration'},
        {'name': 'errors',
         'columnType': 'LARGETEXT'},
        {'name': 'name',
         'columnType': 'STRING',
         'maximumSize': 500},
        {'name': 'versionNumber',
         'columnType': 'STRING',
         'maximumSize': 50},
        {'name': 'fileType',
         'columnType': 'STRING',
         'maximumSize': 50}
    ]

    error_map_cols = [synapseclient.Column(**col) for col in error_col_defs]
    error_schema = synapseclient.Schema(name='Error Table',
                                        columns=error_map_cols,
                                        parent=project)
    error_schema = syn.store(error_schema)

    # Create a table that maps the various database tables to a short name.
    # This table is used in many GENIE functions to find the correct table to update
    # or get the state of something from.

    db_map_col_defs = [
        {'name': 'Database',
         'columnType': 'STRING',
         'maximumSize': 50},
        {'name': 'Id',
         'columnType': 'ENTITYID'}
    ]

    db_map_cols = [synapseclient.Column(**col) for col in db_map_col_defs]
    db_map_schema = synapseclient.Schema(name='DB Mapping Table',
                                         columns=db_map_cols, parent=project)
    db_map_schema = syn.store(db_map_schema)

    # Add the tables we already created to the mapping table.
    dbmap_df = pandas.DataFrame(
        dict(Database=['centerMapping', 'validationStatus', 'errorTracker',
                       'dbMapping', 'logs'], 
             Id=[center_schema.id, status_schema.id, error_schema.id,
                 db_map_schema.id, logs_folder.id])
    )

    db_map_tbl = synapseclient.Table(schema=db_map_schema, values=dbmap_df)
    db_map_tbl = syn.store(db_map_tbl)

    # Make a top level folder for output. Some processing for 
    # file types copy a file from one place to another.
    output_folder = synapseclient.Folder(name='Output', parent=project)
    output_folder = syn.store(output_folder)

    output_folder_map = []

    default_table_col_defs = status_table_col_defs = [
        {'name': 'PRIMARY_KEY',
         'columnType': 'STRING'}
    ]
    default_table_cols = [synapseclient.Column(**col)
                          for col in default_table_col_defs]

    default_primary_key = 'PRIMARY_KEY'

    # For each file type format in the format registry, create an output folder and a table.
    # Some GENIE file types copy a file to a new place, and some update a table. Having both
    # means that both of these operations will be available at the beginning.
    # The mapping between the file type and the folder or table have a consistent naming. 
    # The key ('Database' value) is {file_type}_folder or {file_type}_table.
    for file_type, obj in format_registry.items():
        file_type_folder = synapseclient.Folder(name=file_type,
                                                parent=output_folder)
        file_type_folder = syn.store(file_type_folder)
        output_folder_map.append(dict(Database=f"{file_type}_folder",
                                      Id=file_type_folder.id))
        
        file_type_schema = synapseclient.Schema(name=file_type,
                                                columns=default_table_cols,
                                                parent=project)
        file_type_schema.annotations.primaryKey = default_primary_key
        file_type_schema = syn.store(file_type_schema)

        output_folder_map.append(dict(Database=f"{file_type}_table", 
                                      Id=file_type_schema.id))

    # Add the folders and tables created to the mapping table.
    db_map_tbl = synapseclient.Table(schema=db_map_schema,
                                     values=pandas.DataFrame(output_folder_map))
    db_map_tbl = syn.store(db_map_tbl)
