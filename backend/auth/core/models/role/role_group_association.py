from sqlalchemy import Integer, Table, ForeignKey, Column, UniqueConstraint

from ..base import Base


role_group_role_association = Table('roles_groups_associations', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('role_id', ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
    Column('role_group_id', ForeignKey('roles_groups.id'), nullable=False),
    UniqueConstraint('role_id', 'role_group_id', name='idx_unique_roles_groups'),
    )