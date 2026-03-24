// @ts-nocheck
import React from 'react';
import { useDocuments } from '../../hooks/useDocuments';

export const DocumentFeed = () => {
  const { documents } = useDocuments();

  return (
    <div className="space-y-3">
      {documents.length === 0 ? (
        <p className="text-xs text-gray-500 text-center py-4">No recent documents</p>
      ) : (
        documents.slice(0, 5).map((doc) => (
          <div key={doc.id} className="p-2 border-b border-gray-100 flex justify-between items-center text-sm">
            <span className="truncate max-w-[150px]">{doc.file_name}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              doc.status === 'processed' ? 'bg-green-100 text-green-700' : 
              doc.status === 'error' ? 'bg-red-100 text-red-700' : 
              'bg-blue-100 text-blue-700'
            }`}>
              {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
            </span>
          </div>
        ))
      )}
    </div>
  );
};
