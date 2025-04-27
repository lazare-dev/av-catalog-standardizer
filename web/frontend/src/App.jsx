import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import MappingReviewPage from './pages/MappingReviewPage';
import PreviewPage from './pages/PreviewPage';
import ExportPage from './pages/ExportPage';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/mapping-review/:sessionId" element={<MappingReviewPage />} />
        <Route path="/preview/:sessionId" element={<PreviewPage />} />
        <Route path="/export/:sessionId" element={<ExportPage />} />
      </Routes>
    </Router>
  );
}