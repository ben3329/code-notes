from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel


class IntCoordinates(BaseModel):
    x: int
    y: int


class RGBColor(BaseModel):
    r: int = 255
    g: int = 255
    b: int = 255


class RGBAColor(RGBColor):
    a: float = 1


def _as_bgr(color: RGBColor) -> tuple[int, int, int]:
    return (int(color.b), int(color.g), int(color.r))


def draw_point(
    image: cv2.Mat,
    point: IntCoordinates,
    color: RGBColor = RGBColor(),
    radius: int = 2,
) -> None:
    """Draw a filled circle marker at `point`."""
    cv2.circle(image, (int(point.x), int(point.y)), int(radius), _as_bgr(color), -1)


def draw_line(
    image: cv2.Mat,
    point1: IntCoordinates,
    point2: IntCoordinates,
    color: RGBColor = RGBColor(),
    thickness: int = 2,
) -> None:
    """Draw a straight line between `point1` and `point2`."""
    cv2.line(
        image,
        (int(point1.x), int(point1.y)),
        (int(point2.x), int(point2.y)),
        _as_bgr(color),
        int(thickness),
    )


def draw_circle(
    image: cv2.Mat,
    center: IntCoordinates,
    radius: int,
    border_color: RGBColor = RGBColor(),
    fill_color: RGBAColor | None = None,
    thickness: int = 2,
    draw_center_plus: bool = False,
    plus_color: RGBColor | None = None,
    plus_size: int | None = None,
    plus_thickness: int | float | None = None,
) -> None:
    """Draw a circle with optional fill and center marker."""
    # Draw filled circle with alpha blending if requested
    if fill_color is not None and radius > 0:
        a = max(0.0, min(1.0, float(fill_color.a)))
        if a > 0:
            overlay = image.copy()
            cv2.circle(
                overlay,
                (int(center.x), int(center.y)),
                int(radius),
                _as_bgr(fill_color),
                -1,
            )
            # Alpha blend overlay back onto image in-place
            cv2.addWeighted(overlay, a, image, 1 - a, 0, dst=image)

    # Optionally draw a '+' marker at the center
    if draw_center_plus and radius > 0:
        size = plus_size if plus_size is not None else max(1, int(radius * 0.2))
        p_thick = (
            plus_thickness
            if plus_thickness is not None
            else max(1, int(thickness // 2) or 1)
        )
        pc = plus_color if plus_color is not None else border_color
        plus_bgr = _as_bgr(pc)
        cx, cy = int(center.x), int(center.y)
        # Horizontal and vertical lines
        cv2.line(image, (cx - size, cy), (cx + size, cy), plus_bgr, int(p_thick))
        cv2.line(image, (cx, cy - size), (cx, cy + size), plus_bgr, int(p_thick))

    # Draw border
    if thickness != 0 and radius > 0:
        cv2.circle(
            image,
            (int(center.x), int(center.y)),
            int(radius),
            _as_bgr(border_color),
            int(thickness),
        )


def draw_rectangle(
    image: cv2.Mat,
    top_left: IntCoordinates,
    bottom_right: IntCoordinates,
    border_color: RGBColor = RGBColor(),
    fill_color: RGBAColor | None = None,
    thickness: int = 2,
    radius: int = 0,
) -> None:
    """Draw a rectangle (rounded if `radius` > 0) with optional fill."""
    x1, y1 = int(top_left.x), int(top_left.y)
    x2, y2 = int(bottom_right.x), int(bottom_right.y)
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    r = max(0, int(radius))
    w = max(0, x2 - x1)
    h = max(0, y2 - y1)
    if w == 0 or h == 0:
        return
    if r > 0:
        r = min(r, w // 2, h // 2)

    # Draw filled rounded rectangle with alpha blending if requested
    if fill_color is not None:
        a = max(0.0, min(1.0, float(fill_color.a)))
        fill_bgr = _as_bgr(fill_color)
        if a > 0:
            overlay = image.copy()
            if r == 0:
                cv2.rectangle(overlay, (x1, y1), (x2, y2), fill_bgr, -1)
            else:
                # Center rectangle
                cv2.rectangle(overlay, (x1 + r, y1), (x2 - r, y2), fill_bgr, -1)
                # Side rectangles
                cv2.rectangle(overlay, (x1, y1 + r), (x1 + r, y2 - r), fill_bgr, -1)
                cv2.rectangle(overlay, (x2 - r, y1 + r), (x2, y2 - r), fill_bgr, -1)
                # Corner circles
                cv2.circle(overlay, (x1 + r, y1 + r), r, fill_bgr, -1)
                cv2.circle(overlay, (x2 - r, y1 + r), r, fill_bgr, -1)
                cv2.circle(overlay, (x2 - r, y2 - r), r, fill_bgr, -1)
                cv2.circle(overlay, (x1 + r, y2 - r), r, fill_bgr, -1)
            # Alpha blend overlay back onto image in-place
            cv2.addWeighted(overlay, a, image, 1 - a, 0, dst=image)

    # Draw border (rounded if radius > 0)
    if thickness != 0:
        t = int(thickness)
        border_bgr = _as_bgr(border_color)
        if r == 0:
            cv2.rectangle(image, (x1, y1), (x2, y2), border_bgr, t)
        else:
            # Horizontal edges
            cv2.line(image, (x1 + r, y1), (x2 - r, y1), border_bgr, t)
            cv2.line(image, (x1 + r, y2), (x2 - r, y2), border_bgr, t)
            # Vertical edges
            cv2.line(image, (x1, y1 + r), (x1, y2 - r), border_bgr, t)
            cv2.line(image, (x2, y1 + r), (x2, y2 - r), border_bgr, t)
            # Corner arcs
            cv2.ellipse(image, (x1 + r, y1 + r), (r, r), 0, 180, 270, border_bgr, t)
            cv2.ellipse(image, (x2 - r, y1 + r), (r, r), 0, 270, 360, border_bgr, t)
            cv2.ellipse(image, (x2 - r, y2 - r), (r, r), 0, 0, 90, border_bgr, t)
            cv2.ellipse(image, (x1 + r, y2 - r), (r, r), 0, 90, 180, border_bgr, t)


def write_text(
    image: cv2.Mat,
    text: str,
    org: IntCoordinates,
    *,
    font=cv2.FONT_HERSHEY_SIMPLEX,
    font_scale: float = 1.0,
    color: RGBColor = RGBColor(),
    border_color: RGBColor | None = RGBAColor(r=0, g=0, b=0),
    border_thickness: int | None = None,
    font_path: str | None = None,
    font_size: int | None = None,
    thickness: int = 2,
    line_type=cv2.LINE_AA,
) -> None:
    """Write text using either a TrueType font (via PIL) or OpenCV fonts.

    When `font_path` is provided, this renders onto a minimal RGBA tile and
    alpha-blends it onto the destination to reduce conversions.
    """
    # If a TrueType/OpenType font path is provided, render text on a small RGBA tile
    # to avoid converting the whole image between OpenCV and PIL repeatedly.
    if font_path is not None:

        @lru_cache(maxsize=32)
        def _load_font_cached(path: str, size: int):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                return ImageFont.load_default()

        size = (
            int(font_size)
            if font_size is not None
            else max(1, int(16 * float(font_scale)))
        )
        pil_font = _load_font_cached(font_path, size)

        fill_rgb = (int(color.r), int(color.g), int(color.b))
        if border_color is not None:
            stroke_fill = (
                int(border_color.r),
                int(border_color.g),
                int(border_color.b),
            )
            stroke_width = (
                max(1, int(border_thickness))
                if border_thickness is not None
                else max(1, int(thickness) + 2)
            )
        else:
            stroke_fill = None
            stroke_width = 0

        # Measure text bbox (including stroke) using a tiny temporary draw context
        tmp_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp_img)
        x0, y0, x1, y1 = tmp_draw.textbbox(
            (0, 0), text, font=pil_font, stroke_width=int(stroke_width)
        )
        txt_w, txt_h = max(1, x1 - x0), max(1, y1 - y0)

        # Render text onto its minimal RGBA tile
        text_img = Image.new("RGBA", (txt_w, txt_h), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        text_draw.text(
            (-x0, -y0),
            text,
            font=pil_font,
            fill=fill_rgb,
            stroke_width=int(stroke_width),
            stroke_fill=stroke_fill,
        )

        # Convert the RGBA tile to numpy arrays
        tile_rgba = np.array(text_img)
        if tile_rgba.ndim != 3 or tile_rgba.shape[2] != 4:
            return
        tile_rgb = tile_rgba[:, :, :3]
        tile_bgr = tile_rgb[:, :, ::-1]
        alpha = tile_rgba[:, :, 3].astype(np.float32) / 255.0

        # Compute destination ROI with clipping to image boundaries
        dst_x, dst_y = int(org.x), int(org.y)
        img_h, img_w = image.shape[:2]
        x0_dst = max(0, dst_x)
        y0_dst = max(0, dst_y)
        x1_dst = min(img_w, dst_x + txt_w)
        y1_dst = min(img_h, dst_y + txt_h)

        if x1_dst <= x0_dst or y1_dst <= y0_dst:
            return

        sx0 = x0_dst - dst_x
        sy0 = y0_dst - dst_y
        sx1 = sx0 + (x1_dst - x0_dst)
        sy1 = sy0 + (y1_dst - y0_dst)

        roi = image[y0_dst:y1_dst, x0_dst:x1_dst]
        tile = tile_bgr[sy0:sy1, sx0:sx1]
        a = alpha[sy0:sy1, sx0:sx1]
        a3 = a[..., None]
        # Alpha blend onto the ROI in-place
        roi[:] = (a3 * tile + (1.0 - a3) * roi).astype(np.uint8)
        return

    # Default to OpenCV Hershey fonts
    bgr = _as_bgr(color)
    if border_color is not None:
        border_bgr = _as_bgr(border_color)
        effective_border_thickness = (
            max(1, int(border_thickness))
            if border_thickness is not None
            else max(1, int(thickness) + 2)
        )
        cv2.putText(
            image,
            text,
            (int(org.x), int(org.y)),
            font,
            float(font_scale),
            border_bgr,
            int(effective_border_thickness),
            line_type,
        )
    cv2.putText(
        image,
        text,
        (int(org.x), int(org.y)),
        font,
        float(font_scale),
        bgr,
        int(thickness),
        line_type,
    )
