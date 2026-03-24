import React from 'react';
import { useDocuments } from '../../hooks/useDocuments';
import type { IDocument } from '../../types';

export const DocumentFeed = () => {
  const { documents } = useDocuments();

  return (
    <div className="space-y-3">
      {documents.length === 0 ? (
        <p className="text-xs text-center py-4 text-gray-500">No recent documents</p>
      ) : (
        documents.slice(0, 5).map((doc: IDocument) => (
          <div key={doc.id} className="flex items-center justify-between border-b border-gray-100 p-2 text-sm">
            <span className="max-w-[150px] truncate">{doc.original_file_name || doc.document_type || 'Unknown Document'}</span>
            <span className={`rounded px-2 py-0.5 text-xs ${
              doc.processing_status === 'processed' || doc.processing_status === 'extracted' || doc.processing_status === 'reconciled' ? 'bg-green-100 text-green-700' : 
              doc.processing_status === 'failed' || doc.processing_status === 'flagged' ? 'bg-red-100 text-red-700' : 
              'bg-blue-100 text-blue-700'
            }`}>
              {doc.processing_status ? doc.processing_status.charAt(0).toUpperCase() + doc.processing_status.slice(1) : 'Pending'}
            </span>
          </div>
        ))
      )}
    </div>
  );
};
