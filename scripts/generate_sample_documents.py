"""Create the selectable-text PDF samples used by the local demo."""

from pathlib import Path

from apollo_wheels_mvp.synthetic import write_clean_msa_sample, write_demo_agreements, write_demo_invoice


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_ROOT = PROJECT_ROOT / "samples"

CLIENTS = [
    ("C-1001", "Northstar Fleet Services", "NORTHSTAR"),
    ("C-1002", "Blue River Logistics", "BLUERIVER"),
]

PERIODS = [
    ("JAN", "2026-01-01", "2026-01-31"),
    ("FEB", "2026-02-01", "2026-02-28"),
    ("MAR", "2026-03-01", "2026-03-31"),
]


def main() -> None:
    write_clean_msa_sample(SAMPLE_ROOT / "revised_contracts" / "northstar_master_services_agreement_sample.pdf")
    for client_id, client_name, prefix in CLIENTS:
        client_folder = client_name.replace(" ", "_")
        contract_folder = SAMPLE_ROOT / "contracts" / client_folder
        billing_folder = SAMPLE_ROOT / "billing" / client_folder

        write_demo_agreements(contract_folder, client_id, client_name, prefix)

        for month, start, end in PERIODS:
            for stream in ("SERVICE", "LEASE"):
                invoice_number = f"INV-{client_id}-{month}-{stream}"
                write_demo_invoice(
                    billing_folder / stream.lower(),
                    client_id,
                    client_name,
                    start,
                    end,
                    invoice_number,
                    stream,
                )

    write_demo_agreements(
        SAMPLE_ROOT / "test_uploads" / "Test_Client",
        "C-TEST",
        "Test Client",
        "TEST_CLIENT",
    )


if __name__ == "__main__":
    main()
