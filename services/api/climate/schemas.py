from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class Localized(BaseModel):
    bn: str
    en: str


class PublicationState(StrEnum):
    unavailable = "unavailable"
    provisional = "provisional"
    descriptive_only = "descriptive_only"
    comparison_approved = "comparison_approved"


class Coordinates(BaseModel):
    latitude: Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
    longitude: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]


class Place(BaseModel):
    id: str
    name: Localized
    division: str
    coordinates: Coordinates
    aliases: list[str] = []
    tags: list[str] = []
    featured: bool = True
    feature_type: str = "city"
    country: str = "BD"
    description: Localized
    preview_image_url: str | None = None


class SourceMetadata(BaseModel):
    id: str
    name: str
    version: str
    unit: str
    source_url: str
    citation: str
    spatial_resolution: str
    start: str
    end: str
    retrieved_at: str
    license: str
    notes: Localized


class AnnualObservation(BaseModel):
    year: int
    value: float | None
    complete: bool = True


class MonthlyObservation(BaseModel):
    date: str
    value: float | None


class Comparison(BaseModel):
    baseline_period: str
    recent_period: str
    baseline_value: float
    recent_value: float
    difference: float
    unit: str
    publication_state: PublicationState
    method: Literal["complete-decade-means"] = "complete-decade-means"
    review_id: str
    explanation: Localized


class ClimateComponent(BaseModel):
    series_id: str
    publication_state: PublicationState
    source: SourceMetadata
    annual: list[AnnualObservation] = []
    monthly: list[MonthlyObservation] = []
    comparison: Comparison | None = None
    warning: Localized | None = None
    quality_flags: list[str] = []
    shared_series_with: list[str] = []
    requested_coordinates: Coordinates | None = None
    native_cell_center: Coordinates | None = None
    native_cell_bounds: list[float] | None = None


class GlobalContext(BaseModel):
    source: SourceMetadata
    baseline: str
    annual: list[AnnualObservation]


class ImageryAsset(BaseModel):
    url: str
    thumbnail_url: str
    date: str
    sensor: str
    product_id: str
    source_url: str
    sha256: str
    width: int
    height: int
    bytes: int
    valid_pixel_fraction: float
    scene_cloud_percent: float
    alt: Localized


class ImageryPair(BaseModel):
    id: str
    status: Literal["pending", "needs_review", "approved", "unavailable"]
    before: ImageryAsset | None = None
    after: ImageryAsset | None = None
    bounds: list[float] = []
    crs: str = ""
    resolution_m: int = 30
    attribution: str = (
        "USGS/NASA Landsat. Hosted by Microsoft Planetary Computer; processed by My Climate Story."
    )
    processing_version: str = "landsat-rgb-v1"
    caption: Localized
    review: dict[str, str] | None = None
    error: str | None = None


class QuizQuestion(BaseModel):
    id: str
    category: str
    question: Localized
    options: list[Localized]
    correct_index: int
    explanation: Localized
    source_url: str
    image_question: bool = False


class ActionCard(BaseModel):
    id: str
    tags: list[str]
    audience: Literal["student", "family", "school"]
    title: Localized
    description: Localized
    source_url: str


class ReleaseRef(BaseModel):
    id: str
    created_at: str
    processing_version: str
    content_version: str
    rainfall_pending: bool


class StoryManifest(BaseModel):
    schema_version: Literal[1] = 1
    place: Place
    release: ReleaseRef
    temperature: ClimateComponent
    rainfall: ClimateComponent
    global_context: GlobalContext
    imagery: ImageryPair
    quiz: list[QuizQuestion]
    actions: list[ActionCard]


class ExplorationRequest(BaseModel):
    model_config = {"extra": "forbid"}
    place_id: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    coordinates: Coordinates | None = None

    @model_validator(mode="after")
    def exactly_one_location(self):
        if (self.place_id is None) == (self.coordinates is None):
            raise ValueError("Provide exactly one of place_id or coordinates")
        return self


class JobStatus(BaseModel):
    id: str
    status: Literal["pending", "running", "completed", "failed"]
    story_id: str | None = None
    story_url: str | None = None
    message: str
    retry_after: int = 5


class ExplorationResponse(BaseModel):
    story: StoryManifest | None = None
    job: JobStatus | None = None


class ApiError(BaseModel):
    code: str
    message: str


class PlaceResults(BaseModel):
    results: list[Place]
    coverage_note: Localized
