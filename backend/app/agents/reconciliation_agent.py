from typing import List
from sqlalchemy.orm import Session  # type: ignore
from app.models.transaction import Transaction  # type: ignore
from app.models.anomaly import Anomaly  # type: ignore
from app.services import gstn_service  # type: ignore

class ReconciliationResult:
    def __init__(self, matched: int, mismatches: int, anomalies: List[Anomaly]):
        self.matched = matched
        self.mismatches = mismatches
        self.anomalies = anomalies

class ReconciliationAgent:
    @staticmethod
    async def check_gstr2b(transactions: List[Transaction], client_id: str, gstin: str, 
                           period_month: int, period_year: int, db: Session) -> ReconciliationResult:
        
        # 1. Fetch GSTR-2B data
        gstr2b_data = await gstn_service.fetch_gstr2b(gstin, period_month, period_year)
        b2b_invoices = gstr2b_data.get('b2b', [])
        
        gstr2b_map = {}
        for vendor_data in b2b_invoices:
            v_gstin = vendor_data.get('ctin')
            for inv in vendor_data.get('inv', []):
                key = f"{v_gstin}_{inv.get('inum')}"
                gstr2b_map[key] = inv

        matched_count = 0
        anomalies_list = []

        # 2. Reconcile
        for tx in transactions:
            key = f"{tx.vendor_gstin}_{tx.invoice_number}"
            matched_inv = gstr2b_map.get(key)
            
            if matched_inv:
                # Basic amount check
                gstn_val = float(matched_inv.get('val', 0))
                if abs(float(tx.total_amount) - gstn_val) / max(gstn_val, 1) > 0.01:
                    anomaly = Anomaly(
                        client_id=client_id,
                        ca_firm_id=tx.ca_firm_id,
                        anomaly_type='rate_mismatch',
                        severity='high',
                        description=f"Amount mismatch for {tx.invoice_number}: Extracted {tx.total_amount}, GSTR2B {gstn_val}"
                    )
                    db.add(anomaly)
                    anomalies_list.append(anomaly)
                else:
                    tx.gstr2b_matched = True
                    matched_count += 1  # type: ignore
            else:
                anomaly = Anomaly(
                    client_id=client_id,
                    ca_firm_id=tx.ca_firm_id,
                    anomaly_type='itc_mismatch',
                    severity='high',
                    description=f"Invoice {tx.invoice_number} from {tx.vendor_gstin} not found in GSTR-2B"
                )
                db.add(anomaly)
                anomalies_list.append(anomaly)
                
        db.commit()
        return ReconciliationResult(matched=matched_count, mismatches=len(anomalies_list), anomalies=anomalies_list)
