// src/pages/PreviewPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

export default function PreviewPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState([]);
  const [validation, setValidation] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`/preview/${sessionId}`).then(res => res.json()),
      fetch(`/validation/${sessionId}`).then(res => res.json())
    ]).then(([d, v]) => {
      setData(d);
      setValidation(v);
      setLoading(false);
    });
  }, [sessionId]);

  if (loading) return <div className="container py-5">Loading...</div>;

  return (
    <div className="container py-5">
      <h1>Preview & Validation</h1>
      {/* TODO: Render data table and validation summary using `data` and `validation` */}
      <button className="btn btn-success" onClick={() => navigate(`/export/${sessionId}`)}>
        Continue to Export
      </button>
    </div>
  );
}