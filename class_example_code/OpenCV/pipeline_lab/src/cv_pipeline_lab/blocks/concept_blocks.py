from __future__ import annotations

from typing import Any

from cv_pipeline_lab.blocks.base import BlockBase
from cv_pipeline_lab.core.types import BlockSpec, ParamSpec, RunContext


class _ConceptBlock(BlockBase):
    TYPE_NAME = "ConceptBase"
    TITLE = "Concept"
    MARKDOWN = ""

    @classmethod
    def spec(cls) -> BlockSpec:
        return BlockSpec(
            type_name=cls.TYPE_NAME,
            title=cls.TITLE,
            category="Concept",
            params=[ParamSpec("markdown", "str", cls.MARKDOWN, label="Markdown")],
            description="Draggable concept/teaching annotation block",
            is_concept=True,
        )

    def run(self, inputs: dict[str, Any], params: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
        return {"meta": {"markdown": str(params.get("markdown", self.MARKDOWN))}}

    @classmethod
    def to_snippet(cls, params: dict[str, Any]) -> str:
        text = str(params.get("markdown", cls.MARKDOWN))
        return f"# Concept: {cls.TITLE}\n# {text.replace(chr(10), chr(10) + '# ')}"


class ConceptImageClassificationPipelineBlock(_ConceptBlock):
    TYPE_NAME = "ConceptImageClassificationPipeline"
    TITLE = "Concept: Image Classification Pipeline"
    MARKDOWN = "Preprocess -> Feature extraction -> Classifier"


class ConceptHaarFeaturesBlock(_ConceptBlock):
    TYPE_NAME = "ConceptHaarLikeFeatures"
    TITLE = "Concept: Haar-like Features"
    MARKDOWN = "Haar features compare summed intensities in black/white rectangular regions."


class ConceptAdaBoostBlock(_ConceptBlock):
    TYPE_NAME = "ConceptAdaBoostWeakStrong"
    TITLE = "Concept: AdaBoost Weak->Strong"
    MARKDOWN = "AdaBoost combines weak classifiers into a stronger decision rule by re-weighting errors."


class ConceptCascadeStagesBlock(_ConceptBlock):
    TYPE_NAME = "ConceptCascadeStages"
    TITLE = "Concept: Cascade Stages"
    MARKDOWN = "Early stages reject obvious negatives fast; later stages are more complex."


class ConceptSlidingWindowBlock(_ConceptBlock):
    TYPE_NAME = "ConceptSlidingWindow"
    TITLE = "Concept: Sliding Window"
    MARKDOWN = "Detector scans many windows at multiple scales across the image."


class ConceptHOGBlock(_ConceptBlock):
    TYPE_NAME = "ConceptHOGCellsBlocks3780"
    TITLE = "Concept: HOG Cells/Blocks/3780"
    MARKDOWN = "HOG uses 8x8 cells, 9 bins, 16x16 block normalization; 64x128 gives 3780 features."
