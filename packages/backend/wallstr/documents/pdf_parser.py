import asyncio
import base64
import io
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, cast

import pdf2image
import structlog
from langchain_community.callbacks import get_openai_callback
from langchain_core.messages import HumanMessage
from PIL import Image
from pydantic import BaseModel, Field
from unstructured.chunking import dispatch
from unstructured.documents.elements import Element
from unstructured.partition.pdf import document_to_element_list
from unstructured.partition.pdf_image.pdfminer_processing import (
    clean_pdfminer_inner_elements,
    merge_inferred_with_extracted_layout,
    process_data_with_pdfminer,
)
from unstructured_inference.inference.layout import (
    DocumentLayout,
    process_data_with_model,
)
from unstructured_inference.utils import LayoutElement
from unstructured_ingest.utils.chunking import assign_and_map_hash_ids

from wallstr.conf import settings
from wallstr.core.llm import LLMModel, estimate_input_tokens
from wallstr.core.utils import tiktok

logger = structlog.get_logger()


class Table(BaseModel):
    title: str | None = Field(description="Title of the table")
    data: str = Field(description="Table data in json format")
    content: str = Field(
        description="Summary of the table content that could be used for embedding, explaining the table, omitting the data"
    )


class PdfParser:
    version: int = 1
    inference_model: (
        Literal["yolox"]
        | Literal["yolox_quantized"]
        | Literal["yolox_tiny"]
        # unsupported yet
        | Literal["detectron2_onnx"]
        | Literal["detectron2_quantized"]
        | Literal["detectron2_mask_rcnn"]
    ) = "yolox_quantized"

    def __init__(self, llm: LLMModel, llm_with_vision: LLMModel) -> None:
        self.llm = llm
        self.llm_with_vision = llm_with_vision

    async def parse(self, file_buffer: io.BytesIO) -> list[dict[str, Any]]:
        file_buffer.seek(0)

        async with tiktok(f"Infer the layout with {PdfParser.inference_model} model"):
            loop = asyncio.get_event_loop()
            file_buffer.seek(0)
            inferred_document_layout = await loop.run_in_executor(
                None,
                lambda: process_data_with_model(
                    file_buffer,
                    model_name=PdfParser.inference_model,
                    pdf_image_dpi=200,
                ),
            )

        logger.info("Extract the layout with pdfminer")
        extracted_layout, layouts_links = process_data_with_pdfminer(
            file=file_buffer,
            dpi=200,
        )

        merged_document_layout = merge_inferred_with_extracted_layout(
            inferred_document_layout=inferred_document_layout,
            extracted_layout=extracted_layout,  # type: ignore
            hi_res_model_name=PdfParser.inference_model,
        )
        cleaned_document_layout = clean_pdfminer_inner_elements(merged_document_layout)
        logger.info("Parsing document tables")
        with get_openai_callback() as cb:
            final_document_layout, estimated_tokens = await self._parse_tables_with_llm(
                file_buffer, cleaned_document_layout
            )
            logger.info(
                f"OpenAI tokens used: {cb.total_tokens:_}, cost: {cb.total_cost:.3f}$"
            )
            logger.info(f"OpenAI estimated tokens: {estimated_tokens:_}")
        elements = document_to_element_list(
            final_document_layout,
            sortable=True,
            include_page_breaks=False,
            infer_list_items=False,
            layouts_links=layouts_links,
        )
        logger.info("Chunking the file...")
        chunked_elements = self._chunk(elements)
        chunked_elements_dicts = [e.to_dict() for e in chunked_elements]
        chunked_elements_dicts = assign_and_map_hash_ids(
            elements=chunked_elements_dicts
        )
        return chunked_elements_dicts

    async def _parse_tables_with_llm(
        self, file_buffer: io.BytesIO, layout: DocumentLayout
    ) -> tuple[DocumentLayout, int]:
        async def extract_table_text(image: Image.Image, element: LayoutElement) -> int:
            element.text, estimated_tokens = await self._extract_table_text(
                image, element
            )
            return estimated_tokens

        estimated_tokens = 0
        async with tiktok("Extracting tables from layout"):
            tasks = []
            for page in layout.pages:
                table_elements = [
                    element for element in page.elements if element.type == "Table"
                ]
                if not table_elements:
                    continue

                image = pdf2image.convert_from_bytes(
                    file_buffer.getvalue(),
                    dpi=200,
                    first_page=page.number,
                    last_page=page.number,
                )[0]

                for element in table_elements:
                    tasks.append(extract_table_text(image, element))

            try:
                # TODO: add rate limiting per user
                estimated_tokens = sum(await asyncio.gather(*tasks))
            except Exception as e:
                logger.exception(f"Failed to extract table text: {e}")
        return layout, estimated_tokens

    async def _extract_table_text(
        self, image: Image.Image, element: LayoutElement
    ) -> tuple[str, int]:
        padding = 1
        cropped_image = image.crop(
            (
                element.bbox.x1 + padding,
                element.bbox.y1 + padding,
                element.bbox.x2 + padding,
                element.bbox.y2 + padding,
            )
        )

        if settings.DEBUG:
            debug_dir = Path(".debug")
            debug_dir.mkdir(exist_ok=True)
            filename = f"table_{sha256(cropped_image.tobytes()).hexdigest()}.png"
            cropped_image.save(debug_dir / filename)
            logger.info(f"Saved table image to {filename}")

        image_buffer = io.BytesIO()
        cropped_image.save(image_buffer, format="PNG")
        image_base64 = base64.b64encode(image_buffer.getvalue()).decode("utf-8")
        messages = [
            HumanMessage(
                [
                    {
                        "type": "text",
                        "text": "Extract all data from the image in json format",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ]
            ),
        ]
        estimated_tokens = estimate_input_tokens(
            self.llm_with_vision, messages, image=cropped_image
        )
        logger.info(f"Estimated input tokens: {estimated_tokens:_}")
        try:
            response = await self.llm_with_vision.with_structured_output(Table).ainvoke(
                messages
            )
            response = cast(Table, response)
            logger.debug("Extracted table text", data=response.model_dump())
        except Exception as e:
            logger.error(f"Failed to extract table text: {e}")
            return "", 0

        text = f"""
        Table: {response.title}
        Description:
        {response.content}
        Data:
        {response.data}
        """
        return text, estimated_tokens

    def _chunk(self, elements: list[Element]) -> list[Element]:
        """
        Custom chunking implementation similar to unstructured
        chunked_elements = dispatch.chunk(
            elements=elements, chunking_strategy="by_title", max_characters=2000
        )
        """
        chunked_elements = dispatch.chunk(
            elements=elements, chunking_strategy="by_title", max_characters=2000
        )
        return chunked_elements
