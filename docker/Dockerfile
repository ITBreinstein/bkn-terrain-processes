FROM geopython/pygeoapi:0.23.4

COPY scripts/patch_pygeoapi_openapi.py /pygeoapi/patch_pygeoapi_openapi.py

# pygeoapi 0.23.4 regenerates its OpenAPI file at startup. Apply the narrowly
# scoped v1 compatibility corrections after generation and before Gunicorn.
# Reassess this patch whenever the base image is upgraded.
RUN grep -q 'echo "openapi.yml generated continue to pygeoapi"' /entrypoint.sh \
    && sed -i '/echo "openapi.yml generated continue to pygeoapi"/i \
/venv/bin/python3 /pygeoapi/patch_pygeoapi_openapi.py "${PYGEOAPI_OPENAPI}" --config "${PYGEOAPI_CONFIG}" || exit 1' /entrypoint.sh
