import React from 'react';

export const AnomalyAlerts = () => {
  return (
    <div className="space-y-4">
      <div className="p-3 border-l-4 border-red-500 bg-red-50">
        <p className="text-sm font-bold text-red-700">ITC Mismatch</p>
        <p className="text-xs text-red-600">Client: Ganesh Enterprises. Invoice #1234 not in GSTR-2B.</p>
      </div>
      {/* More stubs as needed */}
    </div>
  );
};
