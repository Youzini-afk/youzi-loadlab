from pydantic import BaseModel, Field


class SecretCreate(BaseModel):
    target_id: str | None = None
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(pattern="^(api_key|admin_password|fireworks_keys|bearer_token|cookie)$")
    plaintext: str = Field(min_length=1)


class SecretRead(BaseModel):
    id: str
    target_id: str | None
    name: str
    kind: str
    fingerprint: str
    masked: str
