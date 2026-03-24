import React, { useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { Shield, UserPlus, Trash2 } from 'lucide-react'

export const UserManagement = () => {
  const rowData = [
    { name: 'John Doe', email: 'john@ca.com', role: 'Partner', status: 'Active' },
    { name: 'Jane Smith', email: 'jane@ca.com', role: 'Staff', status: 'Active' },
    { name: 'Bob Wilson', email: 'bob@ca.com', role: 'Staff', status: 'Invited' },
  ]

  const columnDefs: any = useMemo(() => [
    { field: 'name', headerName: 'Full Name', flex: 1.5 },
    { field: 'email', headerName: 'Email Address', flex: 2 },
    { 
      field: 'role', 
      headerName: 'Role', 
      flex: 1,
      cellRenderer: (p: any) => (
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${p.value === 'Partner' ? 'border-purple-500 text-purple-500' : 'border-slate-600 text-slate-400'}`}>
          {p.value.toUpperCase()}
        </span>
      )
    },
    { 
      field: 'status', 
      headerName: 'Status', 
      flex: 1,
      cellRenderer: (p: any) => (
        <span className={`text-xs font-medium ${p.value === 'Active' ? 'text-emerald-500' : 'text-amber-500'}`}>
          {p.value}
        </span>
      )
    },
    {
      headerName: 'Actions',
      flex: 1,
      cellRenderer: () => (
        <div className="flex items-center space-x-3 mt-2">
          <button className="text-slate-400 hover:text-white" title="Edit Permissions"><Shield size={16} /></button>
          <button className="text-slate-400 hover:text-rose-500" title="Remove User"><Trash2 size={16} /></button>
        </div>
      )
    }
  ], [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Team Management</h2>
          <p className="text-slate-400 text-sm">Manage staff permissions and invites</p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 transition-colors">
          <UserPlus size={18} />
          <span>Invite User</span>
        </button>
      </div>

      <div className="ag-theme-alpine-dark h-[500px] w-full rounded-xl overflow-hidden border border-slate-800">
        <AgGridReact
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={{ resizable: true }}
        />
      </div>
    </div>
  )
}
