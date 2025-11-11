from enum import Enum
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

import boto3


class HTMLTemplateEnum(Enum):
    some_template = "template.html"

    @property
    def path(self) -> str:
        return f"app/assets/html/{self.value}"


class AWSSettings:
    access_key_id: str
    secret_access_key: str
    region: str


config = AWSSettings()


class SES:
    def __init__(self):
        self.ses_client = boto3.client(
            "ses",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        )

    def send_text_email(
        self,
        email_addresses: Sequence[str],
        subject: str,
        body: str,
        *,
        charset: str = "UTF-8",
    ) -> None:
        self._send_simple_email(email_addresses, subject, "Text", body, charset)

    def send_html_email(
        self,
        email_addresses: Sequence[str],
        subject: str,
        body: str,
        *,
        charset: str = "UTF-8",
    ) -> None:
        self._send_simple_email(email_addresses, subject, "Html", body, charset)

    def send_template_email(
        self,
        email_addresses: Sequence[str],
        subject: str,
        template: HTMLTemplateEnum,
        *,
        template_data: Mapping[str, Any] | None = None,
        charset: str = "UTF-8",
    ) -> None:
        html_body = self._render_template(template, template_data)
        self._send_simple_email(email_addresses, subject, "Html", html_body, charset)

    def _send_simple_email(
        self,
        email_addresses: Sequence[str],
        subject: str,
        body_type: Literal["Text", "Html"],
        body: str,
        charset: str,
    ) -> None:
        destination = self._build_destination(email_addresses)
        self.ses_client.send_email(
            Source=config.aws.ses_source,
            Destination=destination,
            Message={
                "Subject": {"Data": subject, "Charset": charset},
                "Body": {body_type: {"Data": body, "Charset": charset}},
            },
        )

    @staticmethod
    def _build_destination(email_addresses: Sequence[str]) -> dict[str, list[str]]:
        to_addresses = list(email_addresses)
        if not to_addresses:
            msg = "At least one recipient address is required."
            raise ValueError(msg)
        return {"ToAddresses": to_addresses}

    @staticmethod
    def _render_template(
        template: HTMLTemplateEnum,
        template_data: Mapping[str, Any] | None,
    ) -> str:
        template_file = Path(template.path)
        if not template_file.is_file():
            msg = f"Template file not found: {template_file}"
            raise FileNotFoundError(msg)

        raw_template = template_file.read_text(encoding="utf-8")

        class _TemplateDict(dict[str, Any]):
            def __missing__(self, key: str) -> str:  # type: ignore[override]
                return "{" + key + "}"

        data = dict(template_data) if template_data else {}
        return raw_template.format_map(_TemplateDict(data))
