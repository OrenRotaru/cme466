from __future__ import annotations

from dataclasses import replace
from typing import Any

from cv_pipeline_lab.blocks.base import BlockBase
from cv_pipeline_lab.blocks.concept_blocks import (
    ConceptAdaBoostBlock,
    ConceptCascadeStagesBlock,
    ConceptHOGBlock,
    ConceptHaarFeaturesBlock,
    ConceptImageClassificationPipelineBlock,
    ConceptSlidingWindowBlock,
)
from cv_pipeline_lab.blocks.detection_blocks import (
    CascadeDetectCustomBlock,
    DetectionStyleDrawBlock,
    DlibHOGFaceDetectBlock,
    HOGDescriptorConfigurableBlock,
    HOGDetectMultiScaleAdvancedBlock,
    HOGDescriptor64x128Block,
    HOGSVMDetectPeopleBlock,
    HaarMultiDetectBlock,
)
from cv_pipeline_lab.blocks.io_blocks import (
    ApplyMaskBlock,
    ChannelMergeBlock,
    ChannelSplitBlock,
    ColorConvertBlock,
    ContourCountBlock,
    DrawDetectionsBlock,
    GrayConvertBlock,
    ImageInputBlock,
    ImageOutputPreviewBlock,
    MergeImageBlock,
    PSNRCompareBlock,
    SaveImageBlock,
    SplitImageBlock,
    VideoFrameInputBlock,
)
from cv_pipeline_lab.blocks.processing_blocks import (
    AdaptiveThresholdBlock,
    BinaryMorphologyBlock,
    CannyEdgeBlock,
    ContrastAdjustmentBlock,
    ContoursAnalysisBlock,
    DenoiseBlurBlock,
    GammaTransformBlock,
    HoughCirclesBlock,
    ImageCropBlock,
    InRangeMaskBlock,
    LogTransformBlock,
    PreprocessPipelineBlock,
    ResizeImageBlock,
    SharpenBlock,
    SimpleThresholdBlock,
    Filter2DBlock,
)
from cv_pipeline_lab.core.types import BlockSpec


class BlockRegistry:
    def __init__(self) -> None:
        self._blocks: dict[str, BlockBase] = {}

    def register(self, block: BlockBase) -> None:
        spec = block.spec()
        self._blocks[spec.type_name] = block

    def has(self, block_type: str) -> bool:
        return block_type in self._blocks

    def get(self, block_type: str) -> BlockBase:
        if block_type not in self._blocks:
            raise KeyError(f"Unknown block type: {block_type}")
        return self._blocks[block_type]

    def get_spec(self, block_type: str) -> BlockSpec:
        return self.get(block_type).spec()

    def all_specs(self) -> list[BlockSpec]:
        specs = [b.spec() for b in self._blocks.values()]
        return sorted(specs, key=lambda s: (s.category, s.title))

    def default_params(self, block_type: str) -> dict[str, Any]:
        spec = self.get_spec(block_type)
        return {p.name: p.default for p in spec.params}

    def to_snippet(self, block_type: str, params: dict[str, Any]) -> str:
        block = self.get(block_type)
        return block.to_snippet(params)

    def normalized_spec(self, block_type: str) -> BlockSpec:
        """Return a spec copy with fully-populated labels."""
        spec = self.get_spec(block_type)
        params = [replace(p, label=p.label or p.name) for p in spec.params]
        return replace(spec, params=params)


def create_default_registry() -> BlockRegistry:
    registry = BlockRegistry()

    # I/O and utility
    registry.register(ImageInputBlock())
    registry.register(VideoFrameInputBlock())
    registry.register(ImageOutputPreviewBlock())
    registry.register(SaveImageBlock())
    registry.register(SplitImageBlock())
    registry.register(MergeImageBlock())
    registry.register(DrawDetectionsBlock())
    registry.register(ContourCountBlock())
    registry.register(ApplyMaskBlock())
    registry.register(ChannelSplitBlock())
    registry.register(ChannelMergeBlock())
    registry.register(PSNRCompareBlock())
    registry.register(GrayConvertBlock())
    registry.register(ColorConvertBlock())

    # Processing
    registry.register(PreprocessPipelineBlock())
    registry.register(ResizeImageBlock())
    registry.register(ImageCropBlock())
    registry.register(ContrastAdjustmentBlock())
    registry.register(LogTransformBlock())
    registry.register(GammaTransformBlock())
    registry.register(InRangeMaskBlock())
    registry.register(DenoiseBlurBlock())
    registry.register(Filter2DBlock())
    registry.register(SharpenBlock())
    registry.register(CannyEdgeBlock())
    registry.register(SimpleThresholdBlock())
    registry.register(AdaptiveThresholdBlock())
    registry.register(BinaryMorphologyBlock())
    registry.register(ContoursAnalysisBlock())
    registry.register(HoughCirclesBlock())

    # Detection
    registry.register(HaarMultiDetectBlock())
    registry.register(HOGDescriptor64x128Block())
    registry.register(HOGDescriptorConfigurableBlock())
    registry.register(HOGSVMDetectPeopleBlock())
    registry.register(HOGDetectMultiScaleAdvancedBlock())
    registry.register(CascadeDetectCustomBlock())
    registry.register(DetectionStyleDrawBlock())
    registry.register(DlibHOGFaceDetectBlock())

    # Concept blocks
    registry.register(ConceptImageClassificationPipelineBlock())
    registry.register(ConceptHaarFeaturesBlock())
    registry.register(ConceptAdaBoostBlock())
    registry.register(ConceptCascadeStagesBlock())
    registry.register(ConceptSlidingWindowBlock())
    registry.register(ConceptHOGBlock())

    return registry
