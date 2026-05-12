import React, { useState } from 'react';
import './FiltersEn.css';

function FiltersEn({
  filters,
  setFilters,
  applyFilters,
  resetFilters,
  contraindicationOptions = [],
}) {
  const [showContra, setShowContra] = useState(false);

  const update = (field, value) => {
    setFilters({ ...filters, [field]: value });
  };

  const toggleContraindication = (value) => {
    const current = Array.isArray(filters.contraindications)
      ? filters.contraindications
      : [];

    const next = current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value];

    update('contraindications', next);
  };

  return (
    <div className="filters-en-card">
      <section className="filters-en-section">
        <h3>Sort by characteristic</h3>

        <select value={filters.sortBy} onChange={(e) => update('sortBy', e.target.value)}>
          <option value="efficacy">Efficacy</option>
          <option value="risk">Risk</option>
          <option value="time">Time to effect</option>
          <option value="cost">Price</option>
        </select>

        <label className="filters-en-radio">
          <input
            type="radio"
            checked={filters.sortOrder === 'desc'}
            onChange={() => update('sortOrder', 'desc')}
          />
          Higher to lower
        </label>

        <label className="filters-en-radio">
          <input
            type="radio"
            checked={filters.sortOrder === 'asc'}
            onChange={() => update('sortOrder', 'asc')}
          />
          Lower to higher
        </label>

        <button type="button" onClick={() => applyFilters(filters)}>
          Apply Filter
        </button>
      </section>

      <section className="filters-en-section">
        <h3>
        Filter by group
        <img
            src="/static/filtros.png"
            alt="Filter icons"
            className="titulo-icone"
        />
        </h3>
        <p>Select your profile so that only treatments indicated for you appear in the list.</p>

        <select value={filters.group} onChange={(e) => update('group', e.target.value)}>
          <option value="all">All</option>
          <option value="children">Children</option>
          <option value="teenagers">Teenagers</option>
          <option value="adults">Adults</option>
          <option value="elderly">Elderly</option>
          <option value="lactating">Lactating</option>
          <option value="pregnancy">Pregnancy</option>
        </select>

        <button type="button" onClick={() => applyFilters(filters)}>
          Apply Filter
        </button>
      </section>

      <section className="filters-en-section">
        <h3>Contraindications <span className="contra-icon">⊘</span></h3>

        <p>Select the conditions you want to avoid in treatments.</p>

        <button type="button" onClick={() => setShowContra((v) => !v)}>
          Select contraindications
        </button>

        {showContra && (
          <div className="filters-en-contra-list">
            {contraindicationOptions.length === 0 ? (
              <span className="filters-en-empty">No contraindications found.</span>
            ) : (
              contraindicationOptions.map((item) => (
                <label key={item} className="filters-en-checkbox">
                  <input
                    type="checkbox"
                    checked={(filters.contraindications || []).includes(item)}
                    onChange={() => toggleContraindication(item)}
                  />
                  {item}
                </label>
              ))
            )}
          </div>
        )}

        <button type="button" onClick={() => applyFilters(filters)}>
          Apply Filter
        </button>
      </section>

      <button type="button" className="filters-en-clear" onClick={resetFilters}>
        Clear all filters
      </button>
    </div>
  );
}

export default FiltersEn;