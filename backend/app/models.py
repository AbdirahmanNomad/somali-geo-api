from typing import Any, Dict, List, Optional
from sqlmodel import Field, Relationship, SQLModel, JSON

# Database base for table creation
from sqlmodel import SQLModel as Base


# Somalia Geography Models

# Shared properties for Region
class RegionBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    code: str = Field(index=True, max_length=10)  # e.g., "SOM-BNR"
    population: Optional[int] = None
    area_km2: Optional[float] = None
    geometry: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)  # GeoJSON geometry


class RegionCreate(RegionBase):
    pass


class RegionUpdate(RegionBase):
    name: Optional[str] = None
    code: Optional[str] = None


class Region(RegionBase, table=True):
    id: int = Field(default=None, primary_key=True)
    districts: List["District"] = Relationship(back_populates="region", cascade_delete=True)


class RegionPublic(RegionBase):
    id: int


class RegionsPublic(SQLModel):
    data: List[RegionPublic]
    count: int


# Shared properties for District
class DistrictBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    code: str = Field(index=True, max_length=20)  # e.g., "SOM-HSH-BLTWYN"
    region_name: str = Field(index=True, max_length=255)
    population: Optional[int] = None
    aliases: Optional[List[str]] = Field(default=None, sa_type=JSON)
    centroid: Optional[Dict[str, float]] = Field(default=None, sa_type=JSON)  # {"lat": float, "lon": float}
    geometry: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)  # GeoJSON geometry


class DistrictCreate(DistrictBase):
    pass


class DistrictUpdate(DistrictBase):
    name: Optional[str] = None
    code: Optional[str] = None
    region_name: Optional[str] = None


class District(DistrictBase, table=True):
    id: int = Field(default=None, primary_key=True)
    region_id: int = Field(foreign_key="region.id", nullable=False)
    region: Region = Relationship(back_populates="districts")


class DistrictPublic(DistrictBase):
    id: int
    region_id: int


class DistrictsPublic(SQLModel):
    data: List[DistrictPublic]
    count: int


# Shared properties for Road
class RoadBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    type: str = Field(max_length=50)  # primary, secondary, etc.
    length_km: Optional[float] = None
    condition: Optional[str] = Field(max_length=50)  # good, fair, poor
    surface: Optional[str] = Field(max_length=50)  # paved, unpaved
    geometry: Optional[List[List[float]]] = Field(default=None, sa_type=JSON)  # [[lon, lat], [lon, lat], ...]


class RoadCreate(RoadBase):
    pass


class RoadUpdate(RoadBase):
    name: Optional[str] = None
    type: Optional[str] = None


class Road(RoadBase, table=True):
    id: int = Field(default=None, primary_key=True)


class RoadPublic(RoadBase):
    id: int


class RoadsPublic(SQLModel):
    data: List[RoadPublic]
    count: int


# Location Code models
class LocationCodeGenerate(SQLModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class LocationCodeResolve(SQLModel):
    code: str


class LocationCodeResponse(SQLModel):
    code: str
    latitude_center: float
    longitude_center: float
    region_code: Optional[str] = None  # e.g., "SOM-BNR"


# Search models
class PlaceSearch(SQLModel):
    name: str
    limit: Optional[int] = 10


class PlaceSearchResult(SQLModel):
    id: str
    name: str
    region: str
    type: str  # district, region, etc.
    aliases: Optional[List[str]] = None
    centroid: Optional[Dict[str, float]] = None
    population: Optional[int] = None


class PlacesSearchResponse(SQLModel):
    data: List[PlaceSearchResult]
    count: int


# Transport infrastructure models
class AirportBase(SQLModel):
    name: str = Field(max_length=255)
    iata_code: Optional[str] = Field(max_length=3)
    icao_code: Optional[str] = Field(max_length=4)
    type: str = Field(max_length=50)  # international, domestic, etc.
    latitude: float
    longitude: float
    region: str = Field(max_length=255)


class Airport(AirportBase, table=True):
    id: int = Field(default=None, primary_key=True)


class AirportPublic(AirportBase):
    id: int


class AirportsPublic(SQLModel):
    data: List[AirportPublic]
    count: int


class PortBase(SQLModel):
    name: str = Field(max_length=255)
    type: str = Field(max_length=50)  # commercial, fishing, etc.
    latitude: float
    longitude: float
    region: str = Field(max_length=255)


class Port(PortBase, table=True):
    id: int = Field(default=None, primary_key=True)


class PortPublic(PortBase):
    id: int


class PortsPublic(SQLModel):
    data: List[PortPublic]
    count: int


class CheckpointBase(SQLModel):
    name: str = Field(max_length=255)
    type: str = Field(max_length=50)  # border, security, etc.
    latitude: float
    longitude: float
    region: str = Field(max_length=255)
    status: str = Field(max_length=50)  # active, inactive


class Checkpoint(CheckpointBase, table=True):
    id: int = Field(default=None, primary_key=True)


class CheckpointPublic(CheckpointBase):
    id: int


class CheckpointsPublic(SQLModel):
    data: List[CheckpointPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# User and Authentication Models (from template)
from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str | None = None


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    email: str | None = None
    password: str | None = None


class UserUpdateMe(SQLModel):
    full_name: str | None = None
    email: str | None = None


class UpdatePassword(SQLModel):
    current_password: str
    new_password: str


class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True)
    hashed_password: str


class UserPublic(UserBase):
    id: int


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UserRegister(SQLModel):
    email: str
    password: str
    full_name: str | None = None


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class NewPassword(SQLModel):
    token: str
    new_password: str


# Item Model (for template compatibility - simple CRUD example)
class ItemBase(SQLModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = None
    description: str | None = None


class Item(ItemBase, table=True):
    id: int = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")


class ItemPublic(ItemBase):
    id: int
    owner_id: int


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int
