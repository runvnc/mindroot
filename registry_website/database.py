from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey, UniqueConstraint, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime

DATABASE_URL = "sqlite:///./mindroot_registry.db"  # Updated database name

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to content
    content = relationship("Content", back_populates="owner")

class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    category = Column(String, index=True)  # 'plugin' or 'agent'
    content_type = Column(String)  # 'mindroot_plugin', 'mindroot_agent'
    data = Column(JSON)  # Plugin/agent specific data
    version = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # MindRoot-specific fields
    github_url = Column(String)
    pypi_module = Column(String)
    commands = Column(JSON)  # List of commands
    services = Column(JSON)  # List of services
    tags = Column(JSON)  # List of tags for categorization
    dependencies = Column(JSON)  # List of dependencies
    
    # Statistics
    download_count = Column(Integer, default=0)
    install_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="content")
    ratings = relationship("Rating", back_populates="content")

    __table_args__ = (UniqueConstraint('title', 'version', name='unique_title_version'),)

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)  # 1-5 stars
    review = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content = relationship("Content", back_populates="ratings")
    user = relationship("User")
    
    __table_args__ = (UniqueConstraint('content_id', 'user_id', name='unique_user_content_rating'),)

class InstallLog(Base):
    __tablename__ = "install_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Anonymous installs allowed
    ip_address = Column(String)
    user_agent = Column(String)
    installed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content = relationship("Content")
    user = relationship("User")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
Base.metadata.create_all(bind=engine)
