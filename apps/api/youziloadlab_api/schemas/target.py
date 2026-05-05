from pydantic import BaseModel, ConfigDict, Field, field_validator


class InlineSecretCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(pattern="^(api_key|admin_password|fireworks_keys|bearer_token|cookie)$")
    plaintext: str = Field(min_length=1)


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(pattern="^(nashiyard|openai_compatible|generic_http)$")
    base_url: str = Field(min_length=1, max_length=500)
    admin_username: str | None = Field(default=None, max_length=120)
    default_model: str | None = Field(default=None, max_length=200)
    secret: InlineSecretCreate | None = None

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        return value.rstrip("/")


class TargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    kind: str
    base_url: str
    admin_username: str | None
    default_model: str | None
