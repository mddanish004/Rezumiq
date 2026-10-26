"""Base model for API request/response shapes.

Every wire field is camelCase; python fields stay snake_case and aliases convert
both directions.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
