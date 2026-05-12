import React from 'react';
import './HeaderEnFilters.css';

function HeaderEnFilters({ summary }) {
  return (
    <header className="treatments-header">
      <div className="treatments-header-left">
        <img
          src="/static/img/en/logo_ingles.png"
          alt="Telix"
          className="treatments-logo"
        />

        <div className="treatments-title-block">
          <h1>{summary?.title || 'Treatments'}</h1>

          <p className="treatments-subtitle">Treatments sorted and filtered by:</p>

          <p>
            <strong>Group:</strong> {summary?.group || 'All'}
          </p>

          <p>
            <strong>Sorting:</strong> {summary?.sorting || 'None'}
          </p>

          <p>
            <strong>Contraindications:</strong>{' '}
            {summary?.contraindications?.length
              ? summary.contraindications.join(', ')
              : 'None'}
          </p>
        </div>
      </div>

      <div className="treatments-warning-box">
        <strong>Do not self-medicate.</strong>
        <br />
        Consult a healthcare professional.
      </div>
    </header>
  );
}

export default HeaderEnFilters;