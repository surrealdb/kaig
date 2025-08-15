from pydantic import BaseModel, Field, RootModel

from kai_graphora.db.definitions import BaseDocument


class Screenshot(BaseModel):
    id: int
    path_thumbnail: str
    path_full: str


class VideoFormats(BaseModel):
    """480: str and max: str video formats"""

    x_480: str | None = Field(
        alias="480", serialization_alias="480", default=None
    )
    max: str


class Movie(BaseModel):
    id: int
    name: str
    thumbnail: str
    webm: VideoFormats
    mp4: VideoFormats
    highlight: bool


class ReleaseDate(BaseModel):
    coming_soon: bool
    date: str


class Recommendations(BaseModel):
    total: int


class SupportInfo(BaseModel):
    url: str
    email: str


class PCRequirements(BaseModel):
    minimum: str | None = None
    recommended: str | None = None


class Category(BaseModel):
    id: int
    description: str


class Genre(BaseModel):
    id: str
    description: str


class ContentDescriptors(BaseModel):
    ids: list[int]
    notes: str | None = None


class Rating(BaseModel):
    rating_generated: str | None = None
    rating: str | None = None
    required_age: str | None = None
    banned: str | None = None
    use_age_gate: str | None = None
    descriptors: str | None = None


class Package(BaseModel):
    packageid: int
    percent_savings_text: str
    percent_savings: int
    option_text: str
    option_description: str
    can_get_free_license: str  # "0"
    is_free_license: bool
    price_in_cents_with_discount: int


class PackageGroup(BaseModel):
    name: str
    title: str
    description: str
    selection_text: str
    save_text: str
    display_type: int
    is_recurring_subscription: str  # "false"
    subs: list[Package]


class Metacritic(BaseModel):
    score: int
    url: str


class PriceOverview(BaseModel):
    currency: str
    initial: int
    final: int
    discount_percent: int
    initial_formatted: str
    final_formatted: str


class Achievement(BaseModel):
    name: str
    path: str


class Achievements(BaseModel):
    total: int
    highlighted: list[Achievement] = Field(default_factory=list)


class AppData(BaseDocument):
    type: str
    name: str
    steam_appid: int
    required_age: int
    is_free: bool
    controller_support: str | None = None
    content: str = Field(
        alias="detailed_description", serialization_alias="detailed_description"
    )
    about_the_game: str
    short_description: str
    supported_languages: str | None = None
    header_image: str
    capsule_image: str
    capsule_imagev5: str
    website: str | None = None
    pc_requirements: PCRequirements | list[PCRequirements] = Field(
        default_factory=list
    )
    mac_requirements: PCRequirements | list[PCRequirements] = Field(
        default_factory=list
    )
    linux_requirements: PCRequirements | list[PCRequirements] = Field(
        default_factory=list
    )
    legal_notice: str | None = None
    developers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    price_overview: PriceOverview | None = None
    packages: list[int] = Field(default_factory=list)
    package_groups: list[PackageGroup] = Field(default_factory=list)
    platforms: dict[str, bool] = Field(default_factory=dict)
    metacritic: Metacritic | None = None
    categories: list[Category] = Field(default_factory=list)
    genres: list[Genre] = Field(default_factory=list)
    screenshots: list[Screenshot] = Field(default_factory=list)
    recommendations: Recommendations | None = None
    movies: list[Movie] = Field(default_factory=list)
    achievements: Achievements | None = None
    release_date: ReleaseDate
    support_info: SupportInfo
    background: str
    background_raw: str
    content_descriptors: ContentDescriptors
    ratings: dict[str, Rating] | None = None

    class Config:
        # This is good practice for models using aliases. It allows you to
        # create an instance using your Python attribute name ('content') as well.
        validate_by_name = True


class AppDetails(BaseModel):
    success: bool
    data: AppData | None = None


# @dataclass
# class AppDataWithId:
#     appid: int
#     data: AppData


class SteamAppDetails(RootModel):
    """Root model for Steam app details with dynamic app IDs as keys"""

    # Using Dict with app_id as keys
    root: dict[int, AppDetails]

    # Helper methods to access the data
    def get_app_ids(self) -> list[int]:
        """Return all app IDs in the data"""
        return list(self.root.keys())

    def get_app_details(self, app_id: int) -> AppDetails | None:
        """Get app details for a specific app ID"""
        return self.root.get(app_id)

    def get_all_app_details(self) -> dict[int, AppDetails]:
        """Get all app details"""
        return self.root

    # For easier access to first app when there's only one
    @property
    def first_app(self) -> AppDetails | None:
        """Return the first app details (useful when there's only one app in the data)"""
        if self.root:
            first_key = next(iter(self.root))
            return self.root[first_key]
        return None


class AppDescriptor(BaseModel):
    appid: int
    name: str


class AppList(BaseModel):
    apps: list[AppDescriptor]


class AppsListRoot(BaseModel):
    applist: AppList


# Test the pydantic model against sample JSON file
# Usage:
#   uv run python src/demo/models.py data/appdetails.json
if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    # file name from args
    file_name = sys.argv[1]
    file_path = Path(file_name)
    with open(file_path, "r") as f:
        data = json.load(f)

    app_details = SteamAppDetails.model_validate(data)
    app = app_details.first_app
    if app and app.data:
        print(app.data.short_description)
