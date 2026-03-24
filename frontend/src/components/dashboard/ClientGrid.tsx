import React, { useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

interface ClientRow {
  client_name: string;
  gstin: string;
  filing_frequency: string;
  status: string;
  last_filed: string;
}

export const ClientGrid = ({ rowData }: { rowData: ClientRow[] }) => {
  const columnDefs = useMemo(() => [
    { field: 'client_name', headerName: 'Client Name', sortable: true, filter: true, flex: 1 },
    { field: 'gstin', headerName: 'GSTIN', filter: true, width: 180 },
    { field: 'filing_frequency', headerName: 'Type', width: 120 },
    { 
      field: 'status', 
      headerName: 'Filing Status',
      cellRenderer: (params: any) => {
        const colors: any = {
          'filed': 'bg-green-100 text-green-800',
          'pending_documents': 'bg-gray-100 text-gray-800',
          'overdue': 'bg-red-100 text-red-800'
        };
        const colorClass = colors[params.value] || 'bg-blue-100 text-blue-800';
        return <span className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>{params.value}</span>;
      }
    },
    { field: 'last_filed', headerName: 'Last Filed', sortable: true },
  ], []);

  return (
    <div className="ag-theme-alpine w-full" style={{ height: 500 }}>
      <AgGridReact
        rowData={rowData}
        columnDefs={columnDefs}
        pagination={true}
        paginationPageSize={15}
        rowSelection="single"
      />
    </div>
  );
};
