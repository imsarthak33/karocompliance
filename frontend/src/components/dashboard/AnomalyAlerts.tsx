// @ts-nocheck
import React, { useEffect, useState } from 'react';

export const AnomalyAlerts = () => {
  const [anomalies, setAnomalies] = useState([]);

  useEffect(() => {
    // In a real app, this would be a fetch to /api/anomalies
    // For now, we simulate the state that will be populated by the backend
    setAnomalies([
      { id: 1, title: 'ITC Mismatch', detail: 'Client: Ganesh Enterprises. Invoice #1234 not in GSTR-2B.', severity: 'red' },
      { id: 2, title: 'Filing Delay', detail: 'Client: Rahul & Co. GSTR-3B overdue by 5 days.', severity: 'yellow' }
    ]);
  }, []);

  return (
    <div className="space-y-4">
      {anomalies.map((alert) => (
        <div key={alert.id} className={`p-3 border-l-4 ${alert.severity === 'red' ? 'border-red-500 bg-red-50' : 'border-yellow-500 bg-yellow-50'}`}>
          <p className={`text-sm font-bold ${alert.severity === 'red' ? 'text-red-700' : 'text-yellow-700'}`}>{alert.title}</p>
          <p className={`text-xs ${alert.severity === 'red' ? 'text-red-600' : 'text-yellow-600'}`}>{alert.detail}</p>
        </div>
      ))}
    </div>
  );
};
