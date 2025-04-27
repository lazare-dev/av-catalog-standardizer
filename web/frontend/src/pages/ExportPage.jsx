// src/pages/ExportPage.jsx
import React from 'react';
import { useParams } from 'react-router-dom';

export default function ExportPage() {
  const { sessionId } = useParams();
  const formats = ['csv', 'xlsx', 'json'];

  return (
    <div className="container py-5">
      <h1>Export</h1>
      <div className="list-group">
        {formats.map(fmt => (
          <a
            key={fmt}
            href={`/export/${sessionId}?format=${fmt}`}
            className="list-group-item list-group-item-action"
          >
            Download {fmt.toUpperCase()}
          </a>
        ))}
      </div>
    </div>
  );
}
