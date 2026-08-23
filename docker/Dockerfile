FROM geopython/pygeoapi:0.23.4@sha256:c8adf6b8e245d315d937eb06f33c3f1cf867e007871d3ac975c9944371ce720b

LABEL org.opencontainers.image.title="BGT Land-cover Summary API" \
      org.opencontainers.image.description="Synchronous BGT land-cover summary process built on pygeoapi" \
      org.opencontainers.image.version="0.2.0" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="Breinstein Informatiemanagement B.V." \
      org.opencontainers.image.base.name="docker.io/geopython/pygeoapi:0.23.4"

ENV CONTAINER_PORT=8080 \
    PYTHONPATH=/pygeoapi \
    PYGEOAPI_ASYNCAPI=/tmp/pygeoapi.asyncapi.yml \
    PYGEOAPI_OPENAPI=/tmp/pygeoapi.openapi.yml \
    WSGI_APP=bkn_terrain_processes.app:APP

COPY config/pygeoapi.yml /pygeoapi/local.config.yml
COPY src/bkn_terrain_processes /pygeoapi/bkn_terrain_processes
COPY LICENSE THIRD_PARTY_NOTICES.md /licenses/bkn-terrain-processes/

COPY scripts/patch_pygeoapi_openapi.py /pygeoapi/patch_pygeoapi_openapi.py

# pygeoapi 0.23.4 regenerates its OpenAPI file at startup. Apply the narrowly
# scoped v1 compatibility corrections after generation and before Gunicorn.
# Reassess this patch whenever the base image is upgraded.
RUN grep -q 'echo "openapi.yml generated continue to pygeoapi"' /entrypoint.sh \
    && sed -i '/echo "openapi.yml generated continue to pygeoapi"/i \
/venv/bin/python3 /pygeoapi/patch_pygeoapi_openapi.py "${PYGEOAPI_OPENAPI}" --config "${PYGEOAPI_CONFIG}" || exit 1' /entrypoint.sh

RUN /venv/bin/python3 -c \
    'import bkn_terrain_processes; from bkn_terrain_processes.process import BgtLandCoverSummaryProcessor'

USER 10001:10001

EXPOSE 8080
