"""Image processing and serving functions."""

import logging
import struct
import tempfile

from PIL import Image
from aiohttp import hdrs, web
from homeassistant.components.http.static import CACHE_HEADERS
from homeassistant.components.http.view import HomeAssistantView
import requests

from .lv_img_converter import Converter
from .const import DATA_IMAGES, DOMAIN

_LOGGER = logging.getLogger(__name__)


def image_to_rgb565(in_image, size, fitscreen):
    """Transform image to rgb565 format according to LVGL requirements."""

    out_image = tempfile.NamedTemporaryFile(mode="w+b")

    conv = Converter(
        in_image, out_image.name, True, Converter.FLAG.CF_TRUE_COLOR_ALPHA, True, size, fitscreen)
    

    conv.convert(Converter.FLAG.CF_TRUE_COLOR_565, 1)
    out_image.write(conv.get_bin_file(Converter.FLAG.CF_TRUE_COLOR_ALPHA))

    _LOGGER.debug(
        "image_to_rgb565 out_image: %s - %s > %s",
        out_image.name
    )

    out_image.flush()

    return out_image


class ImageServeView(HomeAssistantView):
    """View to download images."""

    url = "/api/openhasp/serve/{image_id}"
    name = "api:openhasp:serve"
    requires_auth = False

    def __init__(self) -> None:
        """Initialize image serve view."""

    async def get(self, request: web.Request, image_id: str):
        """Serve image."""

        hass = request.app["hass"]
        target_file = hass.data[DOMAIN][DATA_IMAGES].get(image_id)
        if target_file is None:
            _LOGGER.error("Unknown image_id %s", image_id)
            return web.HTTPNotFound()

        _LOGGER.debug("Get Image %s form %s", image_id, target_file.name)

        return web.FileResponse(
            target_file.name, headers={**CACHE_HEADERS, hdrs.CONTENT_TYPE: "image/bmp"}
        )
