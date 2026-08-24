import tempfile
import unittest
from pathlib import Path

from report_mailer import create_pdf


class ReportPdfTest(unittest.TestCase):
    def test_pdf_has_pdf_header(self):
        with tempfile.TemporaryDirectory() as folder:
            path = create_pdf("Pilot summary", Path(folder) / "report.pdf")
            self.assertTrue(path.read_bytes().startswith(b"%PDF-1.4"))


if __name__ == "__main__":
    unittest.main()
