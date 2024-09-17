from pydantic import BaseModel, ConfigDict

class BaseLibraryModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra="ignore",
        revalidate_instances="always",
        validate_default=True,
        validate_return=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        allow_inf_nan=False,
    )
