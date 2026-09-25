ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Overlay the endpoint's existing ComfyUI image. The base image already ships
# native local-inference MiniMax H3 support (comfy_extras/nodes_minimax_h3.py)
# and KJNodes — it is the same image family as the "MiniMax H3" RunPod Pod
# template. We only replace the handler here; model weights are added by a
# separate, manual build (see Dockerfile.baked + README.md) because they are
# ~41GB and must never be committed to this git repo / built by CI.
#
# NOTE: this used to also overlay a runpod_minimax_compat custom node that
# faked ComfyUI's hidden auth context to call the *cloud-billed* Comfy
# Partner Node (comfy_api_nodes.nodes_minimax.MinimaxHailuo03FirstLastFrameNode).
# That was the wrong target: the actual local-inference "MiniMax H3" the Pod
# runs never touches comfy.org auth or credits. That overlay is intentionally
# dropped; see runpod_minimax_compat/ in git history if it's ever needed again.
COPY handler.py /handler.py
