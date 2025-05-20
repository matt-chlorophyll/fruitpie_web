from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Text
from sqlalchemy.orm import relationship

import database # Import Base from our database.py - direct import

class User(database.Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_poster = Column(Boolean, default=False)
    is_seeker = Column(Boolean, default=True)
    disabled = Column(Boolean, default=False)

    # Relationship to JobPost (if a user can have multiple job posts)
    # This is optional for now if we don't immediately need to navigate from User to their JobPosts
    # job_posts = relationship("JobPost", back_populates="owner") 

class JobPost(database.Base):
    __tablename__ = "job_posts"

    id = Column(Integer, primary_key=True, index=True)
    posted_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="Hiring")
    title = Column(String, index=True, nullable=False)
    company = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    salary = Column(String, nullable=True) # Optional
    contact = Column(String, nullable=False)
    notes = Column(Text, nullable=True) # Optional

    # Optional: If you want to link jobs to a user who posted them
    # owner_id = Column(Integer, ForeignKey("users.id"))
    # owner = relationship("User", back_populates="job_posts") 