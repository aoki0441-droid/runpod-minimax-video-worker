"""Flat-input compatibility node for MiniMax H3 Max API workflows."""

from types import SimpleNamespace

from comfy_api_nodes.nodes_minimax import MinimaxHailuo03FirstLastFrameNode


class RunPodMinimaxH3MaxI2VNode:
    """Avoid DynamicCombo serialization issues in headless ComfyUI execution."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "first_frame": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "seed": (
                    "INT",
                    {
                        "default": 42,
                        "min": 0,
                        "max": 4_294_967_295,
                        "step": 1,
                        "control_after_generate": True,
                    },
                ),
            },
            "hidden": {
                "auth_token_comfy_org": "AUTH_TOKEN_COMFY_ORG",
                "api_key_comfy_org": "API_KEY_COMFY_ORG",
                "unique_id": "UNIQUE_ID",
                "comfy_usage_source": "COMFY_USAGE_SOURCE",
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "execute"
    CATEGORY = "RunPod/MiniMax"
    OUTPUT_NODE = False

    async def execute(
        self,
        first_frame,
        prompt,
        seed,
        auth_token_comfy_org=None,
        api_key_comfy_org=None,
        unique_id=None,
        comfy_usage_source=None,
    ):
        model = {
            "model": "MiniMax H3 Max",
            "prompt": prompt,
            "resolution": "768P",
            "duration": 5,
            "prompt_expansion_mode": "balanced",
        }
        node_class = type(self)
        node_class.hidden = SimpleNamespace(
            auth_token_comfy_org=auth_token_comfy_org,
            api_key_comfy_org=api_key_comfy_org,
            unique_id=unique_id,
            comfy_usage_source=comfy_usage_source,
            dynprompt=None,
        )
        return await MinimaxHailuo03FirstLastFrameNode.execute.__func__(
            node_class,
            model=model,
            first_frame=first_frame,
            seed=seed,
            watermark=False,
        )


NODE_CLASS_MAPPINGS = {
    "RunPodMinimaxH3MaxI2VNode": RunPodMinimaxH3MaxI2VNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RunPodMinimaxH3MaxI2VNode": "RunPod MiniMax H3 Max Image to Video",
}
