import React, { useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, ICellRendererParams } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

interface MismatchRow {
  client_name: string;
  invoice_number: string;
  vendor_name: string;
  extracted_amount: string | number;
  gstr2b_amount: string | number;
  issue_type: string;
  severity: string;
}

export const ReconciliationTable = ({ mismatches }: { mismatches: MismatchRow[] }) => {
  const columnDefs = useMemo<ColDef<MismatchRow>[]>(() => [
    { field: 'client_name', headerName: 'Client', rowGroup: true, hide: true },
    { field: 'invoice_number', headerName: 'Invoice #', width: 150 },
    { field: 'vendor_name', headerName: 'Vendor', flex: 1 },
    { field: 'extracted_amount', headerName: 'Our Data (₹)', valueFormatter: (p) => `₹${p.value}` },
    { field: 'gstr2b_amount', headerName: 'GSTR-2B (₹)', valueFormatter: (p) => `₹${p.value}` },
    { field: 'issue_type', headerName: 'Issue', width: 150 },
    { 
      field: 'severity',
      cellRenderer: (p: ICellRendererParams<MismatchRow, string>) => (
        <span className={`px-2 py-1 text-xs font-bold rounded ${p.value === 'high' ? 'bg-red-200 text-red-900' : 'bg-yellow-200 text-yellow-900'}`}>
          {p.value?.toUpperCase()}
        </span>
      )
    }
  ], []);

  return (
    <div className="ag-theme-alpine w-full" style={{ height: 400 }}>
      <AgGridReact
        rowData={mismatches}
        columnDefs={columnDefs}
        groupDisplayType="groupRows"
        animateRows={true}
      />
    </div>
  );
};
