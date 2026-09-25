"""Flat-input compatibility node for MiniMax H3 Max API workflows."""

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
            }
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "execute"
    CATEGORY = "RunPod/MiniMax"
    OUTPUT_NODE = False

    async def execute(self, first_frame, prompt, seed):
        model = {
            "model": "MiniMax H3 Max",
            "prompt": prompt,
            "resolution": "768P",
            "duration": 5,
            "prompt_expansion_mode": "balanced",
        }
        return await MinimaxHailuo03FirstLastFrameNode.execute(
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
