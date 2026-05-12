import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  useCallback,
  useTransition,
  useDeferredValue,
} from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

import HeaderEnFilters from './HeaderEnFilters';
import FiltersEn from './FiltersEn';
import FooterEn from './FooterEn';
import AvisoFinalEn from './AvisoFinalEn';
import './TreatmentsEnFilters.css';

const DJANGO_BASE =
  process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '';

const API_BASE = '/api';
const CACHE_TTL_MS = 10 * 60 * 1000;
const PAGE_SIZE = 24;

const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
  headers: { Accept: 'application/json' },
});

const normalizeKey = (value) =>
  String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

const toNumber = (value) => {
  if (value === null || value === undefined) return null;

  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === 'string') {
    const parsed = parseFloat(value.replace('%', '').trim().replace(',', '.'));
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
};

const isYes = (value) => {
  const normalized = normalizeKey(value);
  return ['yes', 'sim', 's', 'true', '1'].includes(normalized);
};

const slugToLabel = (slug) => {
  const map = {
    migraine: 'Migraine',
    control: 'control',
    'reduction-of-symptoms': 'reduction of symptoms',
    'symptom-reduction': 'reduction of symptoms',
    remission: 'remission',
    prevention: 'prevention',
    cure: 'cure',
  };

  return map[String(slug ?? '').toLowerCase()] || String(slug ?? '').replace(/-/g, ' ');
};

const slugify = (value) =>
  String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');

const extractContraNames = (treatment) => {
  const raw =
    treatment?.contraindications ??
    treatment?.contraindicacoes ??
    treatment?.contraindications_list ??
    treatment?.contraindicationsList;

  if (!raw) return [];

  if (Array.isArray(raw)) {
    return raw
      .map((item) => {
        if (typeof item === 'string') return item;

        return (
          item?.name ??
          item?.nome ??
          item?.title ??
          item?.titulo ??
          item?.contraindication?.name ??
          item?.contraindicacao?.nome ??
          ''
        );
      })
      .map((item) => String(item).trim())
      .filter(Boolean);
  }

  if (typeof raw === 'string') {
    return raw
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
};

const isIndicatedForGroup = (treatment, group) => {
  if (!group || group === 'all') return true;

  const fieldMap = {
    children: 'indicated_children',
    teenagers: 'indicated_teenagers',
    adults: 'indicated_adults',
    elderly: 'indicated_elderly',
    lactating: 'indicated_lactating',
    pregnancy: 'indicated_pregnancy',
  };

  const fieldName = fieldMap[group];
  if (!fieldName) return true;

  return isYes(treatment?.[fieldName]);
};

const formatPercent = (value) => {
  const number = toNumber(value);

  if (number === null) return 'ND';

  return `${number.toFixed(2).replace('.', ',')}%`;
};

const effectUnitMultiplierInMinutes = (treatment) => {
  const unit = normalizeKey(treatment?.effect_time_unit);

  if (unit === 'second' || unit === 'seconds') return 1 / 60;
  if (unit === 'minute' || unit === 'minutes') return 1;
  if (unit === 'hour' || unit === 'hours') return 60;
  if (unit === 'day' || unit === 'days') return 1440;
  if (unit === 'session' || unit === 'sessions') return 10080;
  if (unit === 'week' || unit === 'weeks') return 10080;

  return 1;
};

const effectMinInMinutes = (treatment) => {
  const multiplier = effectUnitMultiplierInMinutes(treatment);
  const min = toNumber(treatment?.effect_time_min);

  if (min !== null) return min * multiplier;

  return null;
};

const effectMaxInMinutes = (treatment) => {
  const multiplier = effectUnitMultiplierInMinutes(treatment);
  const max = toNumber(treatment?.effect_time_max);

  if (max !== null) return max * multiplier;

  return null;
};

const formatEffectTime = (treatment) => {
  const min = treatment?.effect_time_min;
  const max = treatment?.effect_time_max;
  const unit = treatment?.effect_time_unit;

  if (!min && !max) return 'ND';

  if (min && max && String(min) !== String(max)) {
    return `${min} to ${max} ${unit || ''}`.trim();
  }

  return `${min || max} ${unit || ''}`.trim();
};

const groupLabels = {
  all: 'All',
  children: 'Children',
  teenagers: 'Teenagers',
  adults: 'Adults',
  elderly: 'Elderly',
  lactating: 'Lactating',
  pregnancy: 'Pregnancy',
};

const sortLabels = {
  none: 'None',
  efficacy: 'Efficacy',
  risk: 'Risk',
  time: 'Time to effect',
  cost: 'Price',
};

const detailsBtnStyle = {
  opacity: 0.7,
  marginBottom: 12,
};

async function buildRiskMaxMap(treatmentsList, signal) {
  try {
    const ids = (treatmentsList || [])
      .map((treatment) => treatment?.id)
      .filter((id) => Number.isFinite(Number(id)));

    if (!ids.length) return new Map();

    const response = await api.get('/en/treatment-risks/max-by-treatment/', {
      signal,
      params: {
        ids: ids.join(','),
      },
    });

    const rows = Array.isArray(response.data) ? response.data : [];
    const map = new Map();

    for (const row of rows) {
      const treatmentId = Number(row?.treatment_id);
      const riskMax = toNumber(row?.risk_max);

      if (Number.isFinite(treatmentId) && riskMax !== null) {
        map.set(treatmentId, riskMax);
      }
    }

    return map;
  } catch (error) {
    if (error?.name === 'CanceledError' || error?.code === 'ERR_CANCELED') {
      return new Map();
    }

    return new Map();
  }
}

function TreatmentsEnFilters() {
  const { conditionSlug, efficacySlug } = useParams();

  const conditionLabel = slugToLabel(conditionSlug);
  const efficacyLabel = slugToLabel(efficacySlug);

  const CACHE_KEY = `treatments_en_${conditionSlug}_${efficacySlug}_filters_v1`;

  const DEFAULT_FILTERS = {
    conditionLabel,
    efficacyLabel,
    group: 'all',
    contraindications: [],
    sortBy: 'efficacy',
    sortOrder: 'desc',
  };

  const enforceMandatoryFilters = (filters) => ({
    ...filters,
    conditionLabel,
    efficacyLabel,
  });

  const [treatmentsBaseRaw, setTreatmentsBaseRaw] = useState([]);
  const [statsByTreatmentId, setStatsByTreatmentId] = useState(null);
  const [riskMaxById, setRiskMaxById] = useState(null);

  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState(DEFAULT_FILTERS);

  const [loading, setLoading] = useState(true);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [bootError, setBootError] = useState(null);
  const [highlightSortField, setHighlightSortField] = useState(false);

  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [showBackToTop, setShowBackToTop] = useState(false);

  const [isPending, startTransition] = useTransition();
  const deferredAppliedFilters = useDeferredValue(appliedFilters);

  const layoutRef = useRef(null);
  const sidebarWrapperRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setShowBackToTop(window.scrollY > 350);

    onScroll();

    window.addEventListener('scroll', onScroll, { passive: true });

    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = useCallback(() => {
    const element = document.getElementById('top');

    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [deferredAppliedFilters]);

  const summary = useMemo(() => {
    const group = groupLabels[appliedFilters.group] ?? 'All';

    const sortKey = appliedFilters.sortBy ?? 'none';
    const sortOrderText =
      appliedFilters.sortOrder === 'asc' ? 'ascending' : 'descending';

    const sorting =
      sortKey && sortKey !== 'none'
        ? `${sortLabels[sortKey] ?? sortKey} (${sortOrderText})`
        : 'None';

    const contraindications = Array.isArray(appliedFilters.contraindications)
      ? appliedFilters.contraindications.filter(Boolean)
      : [];

    const title = `Treatments for ${efficacyLabel} of ${conditionLabel}`;

    return {
      title,
      group,
      sorting,
      contraindications,
      condition: appliedFilters.conditionLabel,
      efficacy: appliedFilters.efficacyLabel,
    };
  }, [appliedFilters, conditionLabel, efficacyLabel]);

  function readCache() {
    try {
      const raw = sessionStorage.getItem(CACHE_KEY);

      if (!raw) return null;

      const parsed = JSON.parse(raw);

      if (
        !parsed ||
        typeof parsed.ts !== 'number' ||
        Date.now() - parsed.ts > CACHE_TTL_MS ||
        !Array.isArray(parsed.treatmentsBaseRaw) ||
        parsed.treatmentsBaseRaw.length === 0
      ) {
        return null;
      }

      parsed.efficacyArr = Array.isArray(parsed.efficacyArr)
        ? parsed.efficacyArr
        : [];

      parsed.riskArr = Array.isArray(parsed.riskArr)
        ? parsed.riskArr
        : [];

      return parsed;
    } catch {
      return null;
    }
  }

  function writeCache(payload) {
    try {
      const toStore = {
        ts: Date.now(),
        treatmentsBaseRaw: Array.isArray(payload?.treatmentsBaseRaw)
          ? payload.treatmentsBaseRaw
          : [],
        efficacyArr: Array.isArray(payload?.efficacyArr)
          ? payload.efficacyArr
          : [],
        riskArr: Array.isArray(payload?.riskArr)
          ? payload.riskArr
          : [],
      };

      sessionStorage.setItem(CACHE_KEY, JSON.stringify(toStore));
    } catch {}
  }

  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      setBootError(null);
      setLoading(true);

      const cached = readCache();

      if (
        cached?.treatmentsBaseRaw?.length > 0 &&
        Array.isArray(cached?.efficacyArr) &&
        Array.isArray(cached?.riskArr)
      ) {
        setTreatmentsBaseRaw(cached.treatmentsBaseRaw);
        setStatsByTreatmentId(new Map(cached.efficacyArr));
        setRiskMaxById(new Map(cached.riskArr));
        setLoading(false);
        setIsBootstrapping(false);
        return;
      }

      try {
        const [treatmentsResp, efficacyResp] = await Promise.all([
          api.get('/en/treatments-dynamic/', {
            params: {
              condition_slug: conditionSlug,
              efficacy_slug: efficacySlug,
            },
            signal: controller.signal,
          }),

          api.get('/en/efficacy-dynamic/', {
            params: {
              condition_slug: conditionSlug,
              efficacy_slug: efficacySlug,
            },
            signal: controller.signal,
          }),
        ]);

        const asList = (data) =>
          Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];

        const treatments = asList(treatmentsResp.data);
        const efficacy = asList(efficacyResp.data);

        const statsMap = new Map();

        for (const row of efficacy) {
          const treatmentId = Number(row?.treatment_id);

          if (!Number.isFinite(treatmentId)) continue;

          const value = toNumber(row?.percentual_eficacia_calculado ?? row?.efficacy_value);

          if (value === null) continue;

          const current = statsMap.get(treatmentId);

          if (!current) {
            statsMap.set(treatmentId, {
              min: value,
              max: value,
            });
          } else {
            statsMap.set(treatmentId, {
              min: Math.min(current.min, value),
              max: Math.max(current.max, value),
            });
          }
        }

        const filteredBase = [];

        for (const treatment of treatments) {
          const treatmentId = Number(treatment?.id);

          if (!Number.isFinite(treatmentId)) continue;
          if (!statsMap.has(treatmentId)) continue;

          filteredBase.push(treatment);
        }

        const riskMap = await buildRiskMaxMap(filteredBase, controller.signal);

        writeCache({
          treatmentsBaseRaw: filteredBase,
          efficacyArr: Array.from(statsMap.entries()),
          riskArr: Array.from(riskMap.entries()),
        });

        setTreatmentsBaseRaw(filteredBase);
        setStatsByTreatmentId(statsMap);
        setRiskMaxById(riskMap);
      } catch (error) {
        if (error?.name === 'CanceledError' || error?.code === 'ERR_CANCELED') {
          return;
        }

        setBootError(error?.message || 'Failed to prepare the page.');
      } finally {
        setLoading(false);
        setIsBootstrapping(false);
      }
    };

    load();

    return () => controller.abort();
  }, [conditionSlug, efficacySlug]);

  const treatmentsBase = useMemo(() => {
    if (!treatmentsBaseRaw?.length) return [];

    return treatmentsBaseRaw.map((treatment) => {
      const treatmentId = Number(treatment?.id);
      const stats = statsByTreatmentId?.get?.(treatmentId) ?? null;

      const contraNames = extractContraNames(treatment);
      const contraKeys = contraNames.map(normalizeKey).filter(Boolean);
      const contraSet = new Set(contraKeys);

      const priceNumber = toNumber(treatment?.treatment_cost ?? treatment?.cost);
      const priceFormatted =
        priceNumber !== null
          ? priceNumber.toLocaleString('en-US', {
              style: 'currency',
              currency: 'USD',
            })
          : 'ND';

      const riskNumber = riskMaxById?.get?.(treatmentId) ?? toNumber(treatment?.risk);
      const riskFormatted = formatPercentBR(riskNumber);

      const minTime = effectMinInMinutes(treatment);
      const maxTime = effectMaxInMinutes(treatment);

      return {
        ...treatment,
        _treatmentId: treatmentId,
        _stats: stats,
        _contraNames: contraNames,
        _contraSet: contraSet,
        _priceNumber: priceNumber,
        _priceFormatted: priceFormatted,
        _riskNumber: toNumber(riskNumber),
        _riskFormatted: riskFormatted,
        _effectMinMinutes: minTime,
        _effectMaxMinutes: maxTime,
      };
    });
  }, [treatmentsBaseRaw, statsByTreatmentId, riskMaxById]);

  const contraindicationOptions = useMemo(() => {
    const map = new Map();

    for (const treatment of treatmentsBase) {
      const names = treatment?._contraNames || [];

      for (const name of names) {
        const key = normalizeKey(name);

        if (key && !map.has(key)) {
          map.set(key, name);
        }
      }
    }

    return Array.from(map.values()).sort((a, b) => a.localeCompare(b, 'en-US'));
  }, [treatmentsBase]);

  const applyFilters = useCallback(
    (nextFilters = filters, opts = {}) => {
      const safe = enforceMandatoryFilters(nextFilters);

      if (opts.reset) {
        setHighlightSortField(false);
      } else {
        setHighlightSortField(true);
      }

      startTransition(() => {
        setAppliedFilters(safe);
      });
    },
    [filters]
  );

  const resetFilters = useCallback(() => {
    const safe = enforceMandatoryFilters(DEFAULT_FILTERS);

    setFilters(safe);
    setHighlightSortField(false);
    applyFilters(safe, { reset: true });
  }, [applyFilters]);

  const filteredTreatments = useMemo(() => {
    const safeFilters = enforceMandatoryFilters(deferredAppliedFilters);

    const selectedContraindications = (safeFilters.contraindications || [])
      .map(normalizeKey)
      .filter(Boolean);

    const group = safeFilters.group;

    return (treatmentsBase || []).filter((treatment) => {
      if (!treatment?._treatmentId) return false;
      if (!treatment?._stats) return false;

      if (!isIndicatedForGroup(treatment, group)) return false;

      if (selectedContraindications.length > 0) {
        const contraindicationSet = treatment._contraSet;

        for (const contraindication of selectedContraindications) {
          if (contraindicationSet.has(contraindication)) return false;
        }
      }

      return true;
    });
  }, [
    treatmentsBase,
    deferredAppliedFilters.group,
    deferredAppliedFilters.contraindications,
  ]);

  const sortedTreatments = useMemo(() => {
    const safeFilters = enforceMandatoryFilters(deferredAppliedFilters);
    const array = [...filteredTreatments];

    const criterion = safeFilters.sortBy || 'efficacy';
    const order = safeFilters.sortOrder || 'desc';
    const direction = order === 'asc' ? 1 : -1;

    if (criterion === 'none') return array;

    const getValue = (treatment) => {
      if (criterion === 'efficacy') return treatment._stats?.max ?? -Infinity;

      if (criterion === 'time') {
        return Number.isFinite(treatment._effectMaxMinutes)
          ? treatment._effectMaxMinutes
          : Infinity;
      }

      if (criterion === 'cost') {
        return treatment._priceNumber !== null ? treatment._priceNumber : Infinity;
      }

      if (criterion === 'risk') {
        return treatment._riskNumber !== null ? treatment._riskNumber : Infinity;
      }

      return 0;
    };

    array.sort((a, b) => (getValue(a) - getValue(b)) * direction);

    return array;
  }, [
    filteredTreatments,
    deferredAppliedFilters.sortBy,
    deferredAppliedFilters.sortOrder,
  ]);

  const treatmentsToRender = useMemo(() => {
    return sortedTreatments.slice(0, visibleCount);
  }, [sortedTreatments, visibleCount]);

  const pageReady =
    !bootError &&
    !isBootstrapping &&
    !loading &&
    !isPending &&
    Array.isArray(treatmentsBaseRaw) &&
    statsByTreatmentId instanceof Map &&
    statsByTreatmentId.size > 0 &&
    riskMaxById instanceof Map;

  if (bootError) {
    return (
      <div className="treatments-error-container">
        <div className="treatments-error-box">
          <h2>Oops!</h2>
          <p>{bootError}</p>
          <button
            className="treatments-error-button"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!pageReady) {
    return (
      <div className="treatments-loader-container">
        <div className="treatments-loader-spinner" />
        <p className="treatments-loader-text"></p>
      </div>
    );
  }

  const visualCriterion = filters.sortBy;

  return (
    <div className="treatments-page treatments-en-filters-page">
      <div id="top" />

      <HeaderEnFilters summary={summary} />

      <main className="treatments-layout" ref={layoutRef}>
        <aside className="sidebar" ref={sidebarWrapperRef}>
          <FiltersEn
            filters={enforceMandatoryFilters(filters)}
            setFilters={(next) => setFilters(enforceMandatoryFilters(next))}
            applyFilters={applyFilters}
            resetFilters={resetFilters}
            contraindicationOptions={contraindicationOptions}
            lockedMandatory
          />
        </aside>

        <section className="content">
          <div className="treatments-list">
            {sortedTreatments.length === 0 ? (
              <p></p>
            ) : (
              treatmentsToRender.map((treatment, index) => {
                const stats = treatment._stats;

                const efficacyMin = stats ? stats.min : null;
                const efficacyMax = stats ? stats.max : null;

                const widthBar =
                  efficacyMax !== null
                    ? Math.max(0, Math.min(100, efficacyMax))
                    : 0;

                return (
                  <a
                    key={treatment?.id ?? `${treatment?._treatmentId ?? 't'}-${index}`}
                    href={`${DJANGO_BASE}/treatments/${conditionSlug}/${treatment.slug}/?ef=${encodeURIComponent(
                      slugify(efficacyLabel)
                    )}`}
                    className="treatment-card"
                    style={{ textDecoration: 'none' }}
                  >
                    <div className="treatment-content">
                      <div className="treatment-image">
                        <img
                          src={treatment.image || '/default-image.jpg'}
                          alt={treatment.name || 'Image not available'}
                          className="img-fluid"
                          loading="lazy"
                          decoding="async"
                          fetchPriority={index < 2 ? 'high' : 'auto'}
                        />
                      </div>

                      <div className="treatment-info">
                        <h3>{treatment.name}</h3>

                        {Array.isArray(treatment.treatment_type) &&
                          treatment.treatment_type.length > 0 && (
                            <p className="treatment-type">
                              {treatment.treatment_type
                                .map((item) => item.name || item.nome)
                                .filter(Boolean)
                                .join(' • ')}
                            </p>
                          )}

                        <p>
                          <strong>Active ingredient:</strong>{' '}
                          {treatment.active_ingredient || 'ND'}
                        </p>

                        <p>
                          <strong>Manufacturer:</strong> {treatment.manufacturer || 'ND'}
                        </p>

                        <div className="btn mt-2 treatment-details-btn" style={detailsBtnStyle}>
                          view details <span style={{ fontWeight: 'bold' }}>&#8250;</span>
                        </div>

                        <p>{treatment.description_for_list || treatment.description}</p>
                      </div>

                      <div className="efficacy-container">
                        <p className="efficacy-title">
                          Efficacy:{' '}
                          <span className="efficacy-sub">{efficacyLabel}</span>
                        </p>

                        <div className="efficacy-bar-container">
                          <div className="efficacy-filled" style={{ width: `${widthBar}%` }} />
                          <div
                            className="efficacy-marker"
                            style={{ left: `calc(${widthBar}% - 7px)` }}
                          />
                        </div>

                        <p className="efficacy-range">
                          <span className="efficacy-min">
                            {efficacyMin !== null
                              ? `${String(efficacyMin.toFixed(2)).replace('.', ',')} to`
                              : 'ND to'}
                          </span>
                          <span className="efficacy-max">
                            {' '}
                            {efficacyMax !== null
                              ? `${String(efficacyMax.toFixed(2)).replace('.', ',')}%`
                              : 'ND%'}
                          </span>
                        </p>

                        <div
                          className={`variable-field ${
                            visualCriterion === 'cost'
                              ? 'variable-field--inline'
                              : 'variable-field--stack'
                          } ${highlightSortField ? 'variable-field--highlight' : ''}`}
                        >
                          {visualCriterion === 'cost' ? (
                            <div className="time-container">
                              <p className="time-title">Price:</p>
                              <p className="time-value">{treatment._priceFormatted}</p>
                            </div>
                          ) : visualCriterion === 'risk' ? (
                            <>
                              <p className="time-title">Risk of adverse reaction:</p>
                              <p className="time-value">{treatment._riskFormatted}</p>
                            </>
                          ) : (
                            <>
                              <p className="time-title">Time to effect:</p>
                              <p className="time-value">{formatEffectTime(treatment)}</p>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </a>
                );
              })
            )}

            {sortedTreatments.length > visibleCount && (
              <div className="treatments-load-more-wrap">
                <button
                  type="button"
                  onClick={() => setVisibleCount((value) => value + PAGE_SIZE)}
                  className="treatments-load-more-btn"
                >
                  Load more
                </button>
              </div>
            )}

            {showBackToTop && (
              <button
                type="button"
                onClick={scrollToTop}
                className="treatments-back-to-top"
                aria-label="Back to top"
                title="Back to top"
              >
                ↑
              </button>
            )}
          </div>
        </section>
      </main>

      <FooterEn />
      <AvisoFinalEn />
    </div>
  );
}

export default TreatmentsEnFilters;