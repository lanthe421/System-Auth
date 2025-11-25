from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base


class Permission(Base):
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True, index=True)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # Unique constraint on resource + action combination
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uq_resource_action'),
    )
    
    # Relationships
    roles = relationship('Role', secondary='role_permissions', back_populates='permissions')
    users = relationship('User', secondary='user_permissions', back_populates='permissions')
