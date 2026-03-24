"""
Reconciliation Agent — GSTR-2B cross-verification with strict Decimal math.

Strict Mandates:
  • decimal.Decimal for ALL financial comparisons
  • Sentry span tracing
  • Explicit error logging
"""
import logging
from decimal import Decimal
from typing import List

import sentry_sdk  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.transaction import Transaction  # type: ignore
from app.models.anomaly import Anomaly  # type: ignore
from app.services import gstn_service  # type: ignore

logger = logging.getLogger(__name__)

# Tolerance threshold for amount comparison (1%)
_MISMATCH_TOLERANCE = Decimal("0.01")


class ReconciliationResult:
    def __init__(self, matched: int, mismatches: int, anomalies: List[Anomaly]):
        self.matched = matched
        self.mismatches = mismatches
        self.anomalies = anomalies


class ReconciliationAgent:
    @staticmethod
    async def check_gstr2b(
        transactions: List[Transaction],
        client_id: str,
        gstin: str,
        period_month: int,
        period_year: int,
        db: Session,
    ) -> ReconciliationResult:
        with sentry_sdk.start_span(
            op="agent.reconciliation", description="check_gstr2b"
        ) as span:
            span.set_data("gstin", gstin)
            span.set_data("period", f"{period_month}/{period_year}")
            span.set_data("transaction_count", len(transactions))

            try:
                # 1. Fetch GSTR-2B data
                gstr2b_data = await gstn_service.fetch_gstr2b(gstin, period_month, period_year)
                b2b_invoices = gstr2b_data.get("b2b", [])

                gstr2b_map: dict[str, dict] = {}
                for vendor_data in b2b_invoices:
                    v_gstin = vendor_data.get("ctin")
                    for inv in vendor_data.get("inv", []):
                        key = f"{v_gstin}_{inv.get('inum')}"
                        gstr2b_map[key] = inv

                matched_count = 0
                anomalies_list: list[Anomaly] = []

                # 2. Reconcile with strict Decimal math
                for tx in transactions:
                    key = f"{tx.vendor_gstin}_{tx.invoice_number}"
                    matched_inv = gstr2b_map.get(key)

                    if matched_inv:
                        # Convert GSTN value to Decimal for precise comparison
                        gstn_val = Decimal(str(matched_inv.get("val", "0")))
                        tx_amount = Decimal(str(tx.total_amount)) if tx.total_amount is not None else Decimal("0")

                        # Percentage deviation check
                        denominator = max(gstn_val, Decimal("1"))
                        deviation = abs(tx_amount - gstn_val) / denominator

                        if deviation > _MISMATCH_TOLERANCE:
                            anomaly = Anomaly(
                                client_id=client_id,
                                ca_firm_id=tx.ca_firm_id,
                                anomaly_type="rate_mismatch",
                                severity="high",
                                description=(
                                    f"Amount mismatch for {tx.invoice_number}: "
                                    f"Extracted ₹{tx_amount}, GSTR-2B ₹{gstn_val} "
                                    f"(deviation: {deviation:.4f})"
                                ),
                            )
                            db.add(anomaly)
                            anomalies_list.append(anomaly)
                        else:
                            tx.gstr2b_matched = True
                            matched_count += 1
                    else:
                        anomaly = Anomaly(
                            client_id=client_id,
                            ca_firm_id=tx.ca_firm_id,
                            anomaly_type="itc_mismatch",
                            severity="high",
                            description=(
                                f"Invoice {tx.invoice_number} from {tx.vendor_gstin} "
                                f"not found in GSTR-2B"
                            ),
                        )
                        db.add(anomaly)
                        anomalies_list.append(anomaly)

                db.commit()

                span.set_data("matched", matched_count)
                span.set_data("anomalies", len(anomalies_list))
                logger.info(
                    "Reconciliation complete: %d matched, %d anomalies for GSTIN %s",
                    matched_count, len(anomalies_list), gstin,
                )
                return ReconciliationResult(
                    matched=matched_count,
                    mismatches=len(anomalies_list),
                    anomalies=anomalies_list,
                )

            except Exception as e:
                logger.exception("Reconciliation failed for GSTIN %s", gstin)
                sentry_sdk.capture_exception(e)
                raise
