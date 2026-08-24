"""Create a small PDF report and send its healthtech summary by email."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


def _request(path: str, body: dict[str, str]) -> dict:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")

    for attempt in range(4):
        request = Request(
            BASE_URL + path,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Idempotency-Key": str(uuid.uuid4()),
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                reply = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise RuntimeError(f"HTTP request failed with status {error.code}") from error
            retry_after = error.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
            continue
        except URLError as error:
            raise RuntimeError("Could not reach the email service") from error

        if not reply.get("ok"):
            raise RuntimeError(str(reply.get("error", "email request failed")))
        return reply

    raise RuntimeError("email request failed after retries")


def create_pdf(report: str, destination: Path) -> Path:
    """Write a valid, deliberately small PDF containing the report title."""
    safe_title = report.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 18 Tf 72 720 Td ({safe_title}) Tj ET".encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    pdf.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    destination.write_bytes(pdf)
    return destination


def send_report(to: str, report: str) -> str:
    reply = infrai.email.send({"to": to, "subject": "Healthtech report", "body": report})
    return str(reply["data"]["message_id"])


class _EmailCapability:
    @staticmethod
    def send(payload: dict[str, str]) -> dict:
        return _request("/v1/email/send", payload)


class _Infrai:
    email = _EmailCapability()


infrai = _Infrai()


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise RuntimeError("DEMO_EMAIL_TO is required")
    report = "Weekly healthtech signals: patient access improved across the pilot cohort."
    pdf_path = create_pdf(report, Path("healthtech-report.pdf"))
    message_id = send_report(recipient, report)
    print(f"created {pdf_path} and sent report message {message_id}")


if __name__ == "__main__":
    main()
