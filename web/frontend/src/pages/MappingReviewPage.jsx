// src/pages/MappingReviewPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

export default function MappingReviewPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [mappings, setMappings] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/mapping-review/${sessionId}`)
      .then(res => res.json())
      .then(data => {
        setMappings(data.field_mappings);
        setLoading(false);
      });
  }, [sessionId]);

  const handleUpdate = async () => {
    await fetch(`/update-mappings/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mappings }),
    });
    navigate(`/preview/${sessionId}`);
  };

  if (loading) return <div className="container py-5">Loading...</div>;

  return (
    <div className="container py-5">
      <h1>Field Mapping Review</h1>
      {/* TODO: Render mapping cards based on `mappings` */}
      <button className="btn btn-success" onClick={handleUpdate}>Continue</button>
    </div>
  );
}
