from __future__ import annotations

"""
SQLAlchemy ORM tables for database persistence.
These tables map domain models to database tables.
"""
from sqlalchemy import String, Integer, Float, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


# ============= Account Tables (Inheritance) =============
class AccountTable(Base):
    __tablename__ = "accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column("password", String(255))
    contact_number: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="active")
    type: Mapped[str] = mapped_column(String(50))  # discriminator
    
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "account",
    }


class UserTable(AccountTable):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80), default="")
    saved_locations: Mapped[dict] = mapped_column(JSON, default=list)  # List of LocationNode IDs
    home_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    work_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)  # Google OAuth user ID
    
    # Relationships
    user_suggested_routes: Mapped[list["UserSuggestedRouteTable"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    reports: Mapped[list["ReportTable"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    votes: Mapped[list["SuggestionVoteTable"]] = relationship(back_populates="voter", cascade="all, delete-orphan")
    
    __mapper_args__ = {"polymorphic_identity": "user"}


class AdminTable(AccountTable):
    __tablename__ = "admins"
    
    id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), primary_key=True)
    
    __mapper_args__ = {"polymorphic_identity": "admin"}


# ============= Location Table =============
class LocationTable(Base):
    __tablename__ = "locations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    
    # Relationships
    carparks: Mapped[list["CarparkTable"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    bike_sharing_points: Mapped[list["BikeSharingPointTable"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


# ============= Route Tables (Inheritance) =============
class RouteTable(Base):
    __tablename__ = "routes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    start_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    end_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    subtype: Mapped[str] = mapped_column(String(50))  # "recommended", "alternate", "user_suggested"
    transport_mode: Mapped[str] = mapped_column(String(50), default="")
    route_line: Mapped[dict] = mapped_column(JSON, default=list)  # List of LocationNode IDs
    metrics_id: Mapped[int | None] = mapped_column(ForeignKey("metrics.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50))  # discriminator
    
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "route",
    }


class UserSuggestedRouteTable(RouteTable):
    __tablename__ = "user_suggested_routes"
    
    id: Mapped[int] = mapped_column(ForeignKey("routes.id"), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user: Mapped["UserTable"] = relationship(back_populates="user_suggested_routes")
    votes: Mapped[list["SuggestionVoteTable"]] = relationship(back_populates="route", cascade="all, delete-orphan")
    
    __mapper_args__ = {"polymorphic_identity": "user_suggested"}


# ============= Report Tables (Inheritance) =============
class ReportTable(Base):
    __tablename__ = "reports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(50))  # discriminator
    
    # Relationships
    user: Mapped["UserTable"] = relationship(back_populates="reports")
    
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "report",
    }


class TechnicalReportTable(ReportTable):
    __tablename__ = "technical_reports"
    
    id: Mapped[int] = mapped_column(ForeignKey("reports.id"), primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))
    added_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Changed to VARCHAR to store username
    
    __mapper_args__ = {"polymorphic_identity": "technical"}


# ============= Parking Tables =============
class CarparkTable(Base):
    __tablename__ = "carparks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    hourly_rate: Mapped[float] = mapped_column(Float, default=0.0)
    availability: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    location: Mapped["LocationTable"] = relationship(back_populates="carparks")


class BikeSharingPointTable(Base):
    __tablename__ = "bike_sharing_points"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    bikes_available: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    location: Mapped["LocationTable"] = relationship(back_populates="bike_sharing_points")


# ============= Metrics Tables (Inheritance) =============
class MetricsTable(Base):
    __tablename__ = "metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Removed FK to avoid circular dependency
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_time_min: Mapped[float] = mapped_column(Float, default=0.0)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    carbon_kg: Mapped[float] = mapped_column(Float, default=0.0)
    type: Mapped[str] = mapped_column(String(50))  # discriminator
    
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "metrics",
    }


class DrivingMetricsTable(MetricsTable):
    __tablename__ = "driving_metrics"
    
    id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), primary_key=True)
    fuel_liters: Mapped[float] = mapped_column(Float, default=0.0)
    
    __mapper_args__ = {"polymorphic_identity": "driving"}


class PTMetricsTable(MetricsTable):
    __tablename__ = "pt_metrics"
    
    id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), primary_key=True)
    fares: Mapped[float] = mapped_column(Float, default=0.0)
    
    __mapper_args__ = {"polymorphic_identity": "public_transport"}


class WalkingMetricsTable(MetricsTable):
    __tablename__ = "walking_metrics"
    
    id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), primary_key=True)
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    
    __mapper_args__ = {"polymorphic_identity": "walking"}


class CyclingMetricsTable(MetricsTable):
    __tablename__ = "cycling_metrics"
    
    id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), primary_key=True)
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    
    __mapper_args__ = {"polymorphic_identity": "cycling"}


# ============= Traffic Alert Table =============
class TrafficAlertTable(Base):
    __tablename__ = "traffic_alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    obstruction_type: Mapped[str] = mapped_column(String(100))  # Traffic, Accident, Road Closure, Police
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reported_by: Mapped[int | None] = mapped_column(Integer, nullable=True)  # User ID
    delay_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")  # active, resolved, expired
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


# ============= Suggestion Table =============
class SuggestionTable(Base):
    __tablename__ = "suggestions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    added_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    likes: Mapped[int] = mapped_column(Integer, default=0)  # Number of likes
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)  # Location latitude
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)  # Location longitude
    location_name: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Human-readable location name


# ============= User Likes Table =============
class UserLikeTable(Base):
    __tablename__ = "user_likes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("suggestions.id", ondelete="CASCADE"))
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


# ============= Suggestion Vote Table =============
class SuggestionVoteTable(Base):
    __tablename__ = "suggestion_votes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("user_suggested_routes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    vote_type: Mapped[str] = mapped_column(String(20))  # "upvote" or "downvote"
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    route: Mapped["UserSuggestedRouteTable"] = relationship()
    voter: Mapped["UserTable"] = relationship()


# ============= Saved List Table =============
class SavedListTable(Base):
    __tablename__ = "saved_lists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    places: Mapped[list["SavedPlaceTable"]] = relationship(
        back_populates="saved_list", cascade="all, delete-orphan"
    )


# ============= Saved Place Table =============
class SavedPlaceTable(Base):
    __tablename__ = "saved_places"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("saved_lists.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    saved_list: Mapped["SavedListTable"] = relationship(back_populates="places")


# ============= User Route Tables =============
class UserRouteTable(Base):
    __tablename__ = "user_routes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    route_points: Mapped[dict] = mapped_column(JSON, default=list)  # List of {latitude, longitude, order}
    transport_mode: Mapped[str] = mapped_column(String(20), default="walking")
    distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    
    # Relationships
    route_likes: Mapped[list["UserRouteLikeTable"]] = relationship(
        back_populates="route", cascade="all, delete-orphan"
    )


class UserRouteLikeTable(Base):
    __tablename__ = "user_route_likes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("user_routes.id", ondelete="CASCADE"))
    created_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Relationships
    route: Mapped["UserRouteTable"] = relationship(back_populates="route_likes")
