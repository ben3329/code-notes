from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageOps

MASKABLE_BLOCK_TYPES = {"LINE", "WORD"}


class AWSSettings:
    access_key_id: str
    secret_access_key: str
    region: str


config = AWSSettings()


class Textract:
    def __init__(self):
        self.textract_client = boto3.client(
            "textract",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )

    def _detect_document_text(self, document_bytes: bytes) -> list[dict]:
        try:
            response = self.textract_client.detect_document_text(
                Document={"Bytes": document_bytes}
            )
            return response.get("Blocks", [])
        except ClientError as exc:
            raise Exception(f"Textract detect_document_text failed: {exc}") from exc

    def _apply_exif_orientation(self, image_bytes: bytes) -> bytes:
        with Image.open(BytesIO(image_bytes)) as image:
            oriented_image = ImageOps.exif_transpose(image)
            output = BytesIO()
            oriented_image.save(output, format="JPEG")
            return output.getvalue()

    def _get_bounding_boxes(self, detected_blocks: list[dict]) -> list[dict]:
        bounding_boxes = []

        for block in detected_blocks or []:
            if block.get("BlockType") not in MASKABLE_BLOCK_TYPES:
                continue
            geometry = block.get("Geometry") or {}
            bounding_box = geometry.get("BoundingBox")
            if not bounding_box:
                continue
            bounding_boxes.append(bounding_box)

        return bounding_boxes

    def fetch(self, image_bytes: bytes) -> list[dict]:
        self.image_bytes = self._apply_exif_orientation(image_bytes)
        self.detected_blocks = self._detect_document_text(image_bytes)

    def masking_text_regions(self) -> bytes:
        bounding_boxes = self._get_bounding_boxes(self.detected_blocks)
        if not bounding_boxes:
            return self.image_bytes

        with Image.open(BytesIO(self.image_bytes)) as image:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            for bbox in bounding_boxes:
                left = max(0.0, min(1.0, float(bbox.get("Left", 0.0))))
                top = max(0.0, min(1.0, float(bbox.get("Top", 0.0))))
                bbox_width = max(0.0, float(bbox.get("Width", 0.0)))
                bbox_height = max(0.0, float(bbox.get("Height", 0.0)))
                right = max(left, min(1.0, left + bbox_width))
                bottom = max(top, min(1.0, top + bbox_height))
                pixel_box = (
                    int(round(left * width)),
                    int(round(top * height)),
                    int(round(right * width)),
                    int(round(bottom * height)),
                )
                if pixel_box[2] <= pixel_box[0] or pixel_box[3] <= pixel_box[1]:
                    continue
                draw.rectangle(pixel_box, fill="black")

            output = BytesIO()
            image.save(output, format="JPEG")
            return output.getvalue()
