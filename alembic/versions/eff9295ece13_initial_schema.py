"""initial_schema

Revision ID: eff9295ece13
Revises: 
Create Date: 2025-11-25 12:56:19.936712

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import bcrypt


# revision identifiers, used by Alembic.
revision = 'eff9295ece13'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('middle_name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)
    
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_roles_id', 'roles', ['id'], unique=False)
    
    # Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource', 'action', name='uq_resource_action')
    )
    op.create_index('ix_permissions_id', 'permissions', ['id'], unique=False)
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_valid', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sessions_expiry', 'sessions', ['expires_at'], unique=False)
    op.create_index('idx_sessions_user', 'sessions', ['user_id'], unique=False)
    op.create_index('ix_sessions_id', 'sessions', ['id'], unique=False)
    op.create_index('ix_sessions_token_hash', 'sessions', ['token_hash'], unique=True)
    
    # Create association tables
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    
    op.create_table(
        'user_permissions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'permission_id')
    )
    
    # Seed data - Create permissions for mock resources
    permissions_data = [
        # Documents permissions
        {'resource': 'documents', 'action': 'read', 'description': 'Read documents'},
        {'resource': 'documents', 'action': 'create', 'description': 'Create documents'},
        {'resource': 'documents', 'action': 'update', 'description': 'Update documents'},
        {'resource': 'documents', 'action': 'delete', 'description': 'Delete documents'},
        # Projects permissions
        {'resource': 'projects', 'action': 'read', 'description': 'Read projects'},
        {'resource': 'projects', 'action': 'create', 'description': 'Create projects'},
        {'resource': 'projects', 'action': 'update', 'description': 'Update projects'},
        {'resource': 'projects', 'action': 'delete', 'description': 'Delete projects'},
        # Reports permissions
        {'resource': 'reports', 'action': 'read', 'description': 'Read reports'},
        {'resource': 'reports', 'action': 'create', 'description': 'Create reports'},
        {'resource': 'reports', 'action': 'update', 'description': 'Update reports'},
        {'resource': 'reports', 'action': 'delete', 'description': 'Delete reports'},
    ]
    
    # Insert permissions
    permissions_table = sa.table('permissions',
        sa.column('resource', sa.String),
        sa.column('action', sa.String),
        sa.column('description', sa.Text)
    )
    op.bulk_insert(permissions_table, permissions_data)
    
    # Create roles
    roles_table = sa.table('roles',
        sa.column('name', sa.String),
        sa.column('description', sa.Text)
    )
    op.bulk_insert(roles_table, [
        {'name': 'admin', 'description': 'Administrator with full access'},
        {'name': 'user', 'description': 'Default user with read-only access'}
    ])
    
    # Assign all permissions to admin role (role_id=1, permission_ids=1-12)
    role_permissions_table = sa.table('role_permissions',
        sa.column('role_id', sa.Integer),
        sa.column('permission_id', sa.Integer)
    )
    admin_permissions = [{'role_id': 1, 'permission_id': i} for i in range(1, 13)]
    op.bulk_insert(role_permissions_table, admin_permissions)
    
    # Assign read permissions to user role (role_id=2, permission_ids=1,5,9)
    user_permissions = [
        {'role_id': 2, 'permission_id': 1},  # documents:read
        {'role_id': 2, 'permission_id': 5},  # projects:read
        {'role_id': 2, 'permission_id': 9},  # reports:read
    ]
    op.bulk_insert(role_permissions_table, user_permissions)
    
    # Create initial admin user
    # Password: admin123 (hashed with bcrypt)
    admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt(rounds=12))
    users_table = sa.table('users',
        sa.column('first_name', sa.String),
        sa.column('last_name', sa.String),
        sa.column('email', sa.String),
        sa.column('password_hash', sa.String),
        sa.column('is_active', sa.Boolean)
    )
    op.bulk_insert(users_table, [
        {
            'first_name': 'Admin',
            'last_name': 'User',
            'email': 'admin@example.com',
            'password_hash': admin_password.decode('utf-8'),
            'is_active': True
        }
    ])
    
    # Assign admin role to admin user (user_id=1, role_id=1)
    user_roles_table = sa.table('user_roles',
        sa.column('user_id', sa.Integer),
        sa.column('role_id', sa.Integer)
    )
    op.bulk_insert(user_roles_table, [{'user_id': 1, 'role_id': 1}])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('user_permissions')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_index('ix_sessions_token_hash', table_name='sessions')
    op.drop_index('ix_sessions_id', table_name='sessions')
    op.drop_index('idx_sessions_user', table_name='sessions')
    op.drop_index('idx_sessions_expiry', table_name='sessions')
    op.drop_table('sessions')
    op.drop_index('ix_permissions_id', table_name='permissions')
    op.drop_table('permissions')
    op.drop_index('ix_roles_id', table_name='roles')
    op.drop_table('roles')
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
