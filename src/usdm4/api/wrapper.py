from typing import Union
from usdm4.api.api_base_model import ApiBaseModel
from usdm4.api.study import Study


class Wrapper(ApiBaseModel):
    study: Study
    usdmVersion: str
    systemName: Union[str, None] = None
    systemVersion: Union[str, None] = None
