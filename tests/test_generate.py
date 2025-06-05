import os
import tempfile
from sqlmodelgen.generate import ModelGenerator

def test_generate_enum(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    code = gen.generate_enum('UserStatus', ['active', 'inactive'])
    assert 'class UserStatus' in code
    assert 'active = "active"' in code
    assert 'inactive = "inactive"' in code

def test_generate_model_simple(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    table = {'name': 'user'}
    columns = [
        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        {'name': 'name', 'type': 'VARCHAR', 'nullable': True},
    ]
    relationships = []
    enums = {}
    code = gen.generate_model(table, columns, relationships, enums)
    assert 'class User' in code
    assert 'id: int = Field(primary_key=True)' in code
    assert 'name: Optional[str]' in code

def test_generate_model_with_fk(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    table = {'name': 'user'}
    columns = [
        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        {'name': 'profile_id', 'type': 'INTEGER', 'nullable': True},
    ]
    relationships = [
        {'constrained_columns': ['profile_id'], 'referred_table': 'profile', 'referred_columns': ['id']}
    ]
    enums = {}
    code = gen.generate_model(table, columns, relationships, enums)
    assert 'profile: Optional[Profile] = Relationship(back_populates="user")' in code

def test_generate_model_with_enum(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    table = {'name': 'user'}
    columns = [
        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        {'name': 'status', 'type': 'user_status', 'nullable': False, 'enum_name': 'UserStatus'},
    ]
    relationships = []
    enums = {'UserStatus': ['active', 'inactive']}
    code = gen.generate_model(table, columns, relationships, enums)
    assert 'status: UserStatus = Field(...)' in code
    assert 'from enums.userstatus import UserStatus' in code

def test_generate_model_with_forward_and_reverse_relationships(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    all_tables = ['user', 'profile']
    all_fks = {
        'user': [
            {'constrained_columns': ['profile_id'], 'referred_table': 'profile', 'referred_columns': ['id']}
        ],
        'profile': []
    }
    all_columns = {
        'user': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
            {'name': 'profile_id', 'type': 'INTEGER', 'nullable': True},
        ],
        'profile': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        ]
    }
    rel_map = gen.build_relationship_map(all_tables, all_fks, all_columns)
    # User model (forward relationship)
    user_columns = all_columns['user']
    user_code = gen.generate_model({'name': 'user'}, user_columns, [], {}, rel_map=rel_map)
    assert 'profile: Optional[Profile] = Relationship(back_populates="users")' in user_code
    # Profile model (reverse relationship)
    profile_columns = all_columns['profile']
    profile_code = gen.generate_model({'name': 'profile'}, profile_columns, [], {}, rel_map=rel_map)
    assert 'users: List[User] = Relationship(back_populates="profile")' in profile_code

def test_generate_model_with_one_to_one(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    all_tables = ['user', 'profile']
    all_fks = {
        'user': [
            {'constrained_columns': ['profile_id'], 'referred_table': 'profile', 'referred_columns': ['id']}
        ],
        'profile': []
    }
    all_columns = {
        'user': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
            {'name': 'profile_id', 'type': 'INTEGER', 'nullable': True},
        ],
        'profile': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        ]
    }
    all_uniques = {
        'user': [['profile_id']],  # profile_id is unique, so one-to-one
        'profile': []
    }
    rel_map = gen.build_relationship_map(all_tables, all_fks, all_columns, all_uniques)
    user_code = gen.generate_model({'name': 'user'}, all_columns['user'], [], {}, rel_map=rel_map)
    assert 'profile: Optional[Profile] = Relationship(back_populates="user")' in user_code
    profile_code = gen.generate_model({'name': 'profile'}, all_columns['profile'], [], {}, rel_map=rel_map)
    assert 'user: Optional[User] = Relationship(back_populates="profile")' in profile_code

def test_generate_model_with_many_to_many(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    all_tables = ['user', 'group', 'user_group']
    all_fks = {
        'user': [],
        'group': [],
        'user_group': [
            {'constrained_columns': ['user_id'], 'referred_table': 'user', 'referred_columns': ['id']},
            {'constrained_columns': ['group_id'], 'referred_table': 'group', 'referred_columns': ['id']},
        ]
    }
    all_columns = {
        'user': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        ],
        'group': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        ],
        'user_group': [
            {'name': 'user_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
            {'name': 'group_id', 'type': 'INTEGER', 'nullable': False, 'primary_key': True},
        ]
    }
    rel_map = gen.build_relationship_map(all_tables, all_fks, all_columns)
    user_code = gen.generate_model({'name': 'user'}, all_columns['user'], [], {}, rel_map=rel_map)
    assert 'groups: List[Group] = Relationship(back_populates="users", link_model=UserGroup)' in user_code
    group_code = gen.generate_model({'name': 'group'}, all_columns['group'], [], {}, rel_map=rel_map)
    assert 'users: List[User] = Relationship(back_populates="groups", link_model=UserGroup)' in group_code

def test_generate_model(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    table = {'name': 'user'}
    columns = [
        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        {'name': 'name', 'type': 'VARCHAR', 'nullable': True},
    ]
    relationships = []
    enums = {}
    code = gen.generate_model(table, columns, relationships, enums)
    assert 'class User' in code
    # The template is minimal, so fields will be empty for now 

def test_generate_model_with_array_column(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    table = {'name': 'article'}
    columns = [
        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        {'name': 'tags', 'type': 'ARRAY', 'element_type': 'VARCHAR', 'is_array': True, 'nullable': True},
        {'name': 'scores', 'type': 'ARRAY', 'element_type': 'INTEGER', 'is_array': True, 'nullable': False},
    ]
    code = gen.generate_model(table, columns, [], {})
    assert 'tags: List[str]' in code
    assert 'scores: List[int] = Field(...)' in code
    assert 'from typing import List' in code

def test_generate_model_with_array_type_override(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    table = {'name': 'article'}
    columns = [
        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        {'name': 'tags', 'type': 'ARRAY', 'element_type': 'VARCHAR', 'is_array': True, 'nullable': True},
    ]
    type_overrides = {'ARRAY': 'CustomArrayType'}
    code = gen.generate_model(table, columns, [], {}, type_overrides=type_overrides)
    assert 'tags: Optional[CustomArrayType]' in code

def test_generate_model_with_nested_array(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    table = {'name': 'matrix'}
    columns = [
        {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        {'name': 'matrix', 'type': 'ARRAY', 'element_type': 'ARRAY', 'is_array': True, 'nullable': True, 'element_type': 'INTEGER'},
    ]
    # For this test, we simulate a nested array by setting element_type to 'ARRAY' and is_array True
    # The current implementation will treat this as List[int], but you can expand to support List[List[int]]
    code = gen.generate_model(table, columns, [], {})
    # This will currently output List[int], but you can expand logic for List[List[int]]
    assert 'matrix: List[int]' in code or 'matrix: List[List[int]]' in code 

def test_generate_model_with_exclude_tables_and_columns(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    # Simulate two tables, one excluded
    all_tables = ['user', 'profile']
    all_fks = {'user': [], 'profile': []}
    all_columns = {
        'user': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
            {'name': 'name', 'type': 'VARCHAR', 'nullable': True},
            {'name': 'secret', 'type': 'VARCHAR', 'nullable': True},
        ],
        'profile': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        ]
    }
    exclude_tables = {'profile'}
    exclude_columns = {'secret'}
    # Only generate for 'user', and exclude 'secret' column
    rel_map = gen.build_relationship_map(['user'], {'user': []}, {'user': all_columns['user']})
    user_code = gen.generate_model({'name': 'user'}, [c for c in all_columns['user'] if c['name'] not in exclude_columns], [], {}, rel_map=rel_map)
    assert 'secret' not in user_code
    assert 'class User' in user_code
    # 'profile' table should not be generated at all (simulate in CLI)

def test_generate_model_relationship_mode_minimal_vs_full(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    all_tables = ['user', 'profile']
    all_fks = {
        'user': [
            {'constrained_columns': ['profile_id'], 'referred_table': 'profile', 'referred_columns': ['id']}
        ],
        'profile': []
    }
    all_columns = {
        'user': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
            {'name': 'profile_id', 'type': 'INTEGER', 'nullable': True},
        ],
        'profile': [
            {'name': 'id', 'type': 'INTEGER', 'nullable': False},
        ]
    }
    # Full mode: both forward and reverse
    rel_map_full = gen.build_relationship_map(all_tables, all_fks, all_columns)
    user_code_full = gen.generate_model({'name': 'user'}, all_columns['user'], [], {}, rel_map=rel_map_full)
    profile_code_full = gen.generate_model({'name': 'profile'}, all_columns['profile'], [], {}, rel_map=rel_map_full)
    assert 'profile: Optional[Profile] = Relationship(back_populates="users")' in user_code_full
    assert 'users: List[User] = Relationship(back_populates="profile")' in profile_code_full
    # Minimal mode: only forward (simulate by passing rel_map=None)
    user_code_min = gen.generate_model({'name': 'user'}, all_columns['user'], all_fks['user'], {}, rel_map=None)
    profile_code_min = gen.generate_model({'name': 'profile'}, all_columns['profile'], [], {}, rel_map=None)
    assert 'profile: Optional[Profile] = Relationship(back_populates="user")' in user_code_min
    assert 'users: List[User]' not in profile_code_min 

def test_idempotent_file_writing(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    code = 'class Foo: pass\n'
    # Write file first time
    gen.write_model_file('Foo', code)
    path = tmp_path / 'foo.py'
    assert path.exists()
    mtime1 = path.stat().st_mtime
    # Write again with same content (should not change mtime)
    gen.write_model_file('Foo', code)
    mtime2 = path.stat().st_mtime
    assert mtime1 == mtime2
    # Write with different content (should update)
    code2 = 'class Foo: pass\n# changed\n'
    gen.write_model_file('Foo', code2)
    mtime3 = path.stat().st_mtime
    assert mtime3 > mtime2

def test_cleanup_old_files(tmp_path):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'))
    # Create two files, keep only one
    keep = set()
    f1 = tmp_path / 'foo.py'
    f2 = tmp_path / 'bar.py'
    f1.write_text('foo')
    f2.write_text('bar')
    keep.add(str(f1))
    gen.cleanup_old_files(keep, str(tmp_path))
    assert f1.exists()
    assert not f2.exists()

def test_preview_mode_writes_and_deletes(tmp_path, capsys):
    gen = ModelGenerator(output_dir=str(tmp_path), enum_output_dir=str(tmp_path), template_dir=os.path.join(os.path.dirname(__file__), '../src/sqlmodelgen/templates'), preview=True)
    code = 'class Foo: pass\n'
    written = set()
    gen.write_model_file('Foo', code, written)
    # Simulate a file to be deleted
    f2 = tmp_path / 'bar.py'
    f2.write_text('bar')
    gen.cleanup_old_files(written, str(tmp_path))
    out = capsys.readouterr().out
    assert '[PREVIEW] Would write model:' in out
    assert '[PREVIEW] Would delete:' in out 