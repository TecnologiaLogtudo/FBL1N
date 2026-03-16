import tempfile
import unittest
from pathlib import Path

import pandas as pd

from inverse_processor import OpenTitlesProcessor


class OpenTitlesProcessorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.lookup = {
            "Bahia": pd.DataFrame(
                {
                    "Referência": [123, 456],
                    "Valor pagamento": [100.0, 0.0],
                    "Data de compensação": ["01/02/2025", "03/04/2025"],
                }
            )
        }

    def test_runs_and_generates_summary_and_detail(self):
        df = pd.DataFrame(
            {
                "CTRC": [123, 999],
                "Status": ["Aberto", "Aberto"],
                "Transportadora": ["Logtudo Bahia", ""],
            }
        )
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            temp_path = tmp_file.name
        df.to_excel(temp_path, index=False)
        processor = OpenTitlesProcessor(temp_path)
        summary, detail = processor.run(self.lookup)
        Path(temp_path).unlink(missing_ok=True)

        self.assertIn("Total geral", summary["Transportadora"].values)
        self.assertEqual(len(detail), 2)
        matched_row = detail[detail["CTRC"] == 123].iloc[0]
        self.assertEqual(matched_row["Resultado"], "Pago no FBL1")


if __name__ == "__main__":
    unittest.main()
