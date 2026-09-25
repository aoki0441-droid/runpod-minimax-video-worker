ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Overlay the endpoint's existing ComfyUI image. This preserves its MiniMax
# nodes, credentials, startup script, and model configuration.
COPY handler.py /handler.py
