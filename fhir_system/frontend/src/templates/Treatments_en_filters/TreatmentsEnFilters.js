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

const normalizeKey = (v) =>
  String(v ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();

const slugToLabel = (slug) => {
  const map = {
    migraine: 'Migraine',
    control: 'control',
    'reduction-of-symptoms': 'reduction of symptoms',
    'symptom-reduction': 'reduction of symptoms',
    prevention: 'prevention',
    remission: 'remission',
    cure: 'cure',
  };

  return map[String(slug ?? '').toLowerCase()] || String(slug ?? '').replace(/-/g, ' ');
};

const slugifyEF = (s) =>
  String(s ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');

const toNumber = (v) => {
  if (v === null || v === undefined) return null;
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'string') {
    const s = v.replace('%', '').trim().replace(',', '.');
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : null;
  }
  return null;
};

const isYes = (v) => {
  const n = normalizeKey(v);
  return n === 'yes' || n === 'sim' || n === 's' || n === 'true' || n === '1';
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

  const field = fieldMap[group];
  if (!field) return true;

  return isYes(treatment?.[field]);
};

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
      .map((s) => String(s).trim())
      .filter(Boolean);
  }

  if (typeof raw === 'string') {
    return raw
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  }

  return [];
};

const formatPercent = (n) => {
  if (n === null || n === undefined) return 'ND';
  if (!Number.isFinite(n)) return 'ND';
  return `${n.toFixed(0).replace('.', ',')}%`;
};

const effectUnitMultiplier = (t) => {
  const unit = normalizeKey(t?.effect_time_unit);

  if (unit === 'second' || unit === 'seconds') return 1 / 60;
  if (unit === 'minute' || unit === 'minutes') return 1;
  if (unit === 'hour' || unit === 'hours') return 60;
  if (unit === 'day' || unit === 'days') return 1440;
  if (unit === 'session' || unit === 'sessions') return 10080;
  if (unit === 'week' || unit === 'weeks') return 10080;

  return 1;
};

const effectMinInMinutes = (t) => {
  const min = toNumber(t?.effect_time_min);
  if (min === null) return null;
  return min * effectUnitMultiplier(t);
};

const effectMaxInMinutes = (t) => {
  const max = toNumber(t?.effect_time_max);
  if (max === null) return null;
  return max * effectUnitMultiplier(t);
};

const formatEffectTime = (t) => {
  const min = t?.effect_time_min;
  const max = t?.effect_time_max;
  const unit = t?.effect_time_unit;

  if (!min && !max) return 'ND';

  if (min && max && String(min) !== String(max)) {
    return `${min} to ${max} ${unit || ''}`.trim();
  }

  return `${min || max} ${unit || ''}`.trim();
};

const labelGroup = {
  all: 'All',
  children: 'Children',
  teenagers: 'Teenagers',
  adults: 'Adults',
  elderly: 'Elderly',
  lactating: 'Lactating',
  pregnancy: 'Pregnancy',
};

const labelSorting = {
  none: 'None',
  efficacy: 'Efficacy',
  risk: 'Risk',
  time: 'Time to effect',
  cost: 'Price',
};

const detailsBtnStyle = { opacity: 0.7, marginBottom: 12 };

function TreatmentsEnFilters() {
  const { conditionSlug, efficacySlug } = useParams();

  const CONDITION_LABEL = slugToLabel(conditionSlug);
  const EFFICACY_LABEL = slugToLabel(efficacySlug);

  const CACHE_KEY = `treatments_en_${conditionSlug}_${efficacySlug}_filters_v1`;

  const DEFAULT_FILTERS = {
    conditionLabel: CONDITION_LABEL,
    efficacyLabel: EFFICACY_LABEL,
    group: 'all',
    contraindications: [],
    sortBy: 'efficacy',
    sortOrder: 'desc',
  };

  const enforceMandatoryFilters = (filters) => ({
    ...filters,
    conditionLabel: CONDITION_LABEL,
    efficacyLabel: EFFICACY_LABEL,
  });

  const [treatmentsBaseRaw, setTreatmentsBaseRaw] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [bootError, setBootError] = useState(null);

  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState(DEFAULT_FILTERS);
  const [highlightSortField, setHighlightSortField] = useState(false);

  const [statsByTreatmentId, setStatsByTreatmentId] = useState(null);
  const [riskMaxById, setRiskMaxById] = useState(new Map());

  const [isPending, startTransition] = useTransition();
  const deferredAppliedFilters = useDeferredValue(appliedFilters);

  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const layoutRef = useRef(null);
  const sidebarWrapperRef = useRef(null);

  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    const onScroll = () => setShowBackToTop(window.scrollY > 350);
    onScroll();

    window.addEventListener('scroll', onScroll, { passive: true });

    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = useCallback(() => {
    const el = document.getElementById('top');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [deferredAppliedFilters]);

  const summary = useMemo(() => {
    const group = labelGroup[appliedFilters.group] ?? 'All';

    const sortKey = appliedFilters.sortBy ?? 'none';
    const sortOrderText =
      appliedFilters.sortOrder === 'asc' ? 'ascending' : 'descending';

    const sorting =
      sortKey && sortKey !== 'none'
        ? `${labelSorting[sortKey] ?? sortKey} (${sortOrderText})`
        : 'None';

    const contraindications = Array.isArray(appliedFilters.contraindications)
      ? appliedFilters.contraindications.filter(Boolean)
      : [];

    let title = `Treatments for ${EFFICACY_LABEL} of ${CONDITION_LABEL}`;

    if (conditionSlug === 'migraine' && efficacySlug === 'control') {
      title = 'Treatments for control of migraine';
    }

    return {
      group,
      sorting,
      contraindications,
      condition: appliedFilters.conditionLabel,
      efficacy: appliedFilters.efficacyLabel,
      title,
    };
  }, [
    appliedFilters,
    conditionSlug,
    efficacySlug,
    CONDITION_LABEL,
    EFFICACY_LABEL,
  ]);

  function readCache() {
    try {
      const raw = sessionStorage.getItem(CACHE_KEY);
      if (!raw) return null;

      const parsed = JSON.parse(raw);

      if (
        !parsed ||
        typeof parsed.ts !== 'number' ||
        Date.now() - parsed.ts > CACHE_TTL_MS ||
        !Array.isArray(parsed.treatmentsBaseRaw)
      ) {
        return null;
      }

      parsed.efficacyArr = Array.isArray(parsed.efficacyArr)
        ? parsed.efficacyArr
        : [];

      parsed.riskArr = Array.isArray(parsed.riskArr) ? parsed.riskArr : [];

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
        riskArr: Array.isArray(payload?.riskArr) ? payload.riskArr : [],
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
        cached?.treatmentsBaseRaw &&
        cached?.efficacyArr &&
        cached?.riskArr
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

        for (let i = 0; i < efficacy.length; i++) {
          const row = efficacy[i];

          const treatmentId = Number(row?.treatment_id);
          if (!Number.isFinite(treatmentId)) continue;

          const value = toNumber(
            row?.percentual_eficacia_calculado ?? row?.efficacy_value
          );

          if (value === null) continue;

          const current = statsMap.get(treatmentId);

          if (!current) {
            statsMap.set(treatmentId, { min: value, max: value });
          } else {
            statsMap.set(treatmentId, {
              min: Math.min(current.min, value),
              max: Math.max(current.max, value),
            });
          }
        }

        const filteredBase = [];

        for (let i = 0; i < treatments.length; i++) {
          const treatment = treatments[i];
          const treatmentId = Number(treatment?.id);

          if (!Number.isFinite(treatmentId)) continue;
          if (!statsMap.has(treatmentId)) continue;

          filteredBase.push(treatment);
        }

        const riskMap = new Map();

        filteredBase.forEach((item) => {
          const treatmentId = Number(item?.id);
          const risk = toNumber(item?.risk);

          if (Number.isFinite(treatmentId) && risk !== null) {
            riskMap.set(treatmentId, risk);
          }
        });

        writeCache({
          treatmentsBaseRaw: filteredBase,
          efficacyArr: Array.from(statsMap.entries()),
          riskArr: Array.from(riskMap.entries()),
        });

        setTreatmentsBaseRaw(filteredBase);
        setStatsByTreatmentId(statsMap);
        setRiskMaxById(riskMap);
      } catch (error) {
        if (error?.name === 'CanceledError' || error?.code === 'ERR_CANCELED') return;
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

    const out = new Array(treatmentsBaseRaw.length);

    for (let i = 0; i < treatmentsBaseRaw.length; i++) {
      const treatment = treatmentsBaseRaw[i];

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

      const riskNumber = riskMaxById?.get?.(treatmentId) ?? null;
      const riskFormatted = formatPercent(toNumber(riskNumber));

      const effectMin = effectMinInMinutes(treatment);
      const effectMax = effectMaxInMinutes(treatment);

      out[i] = {
        ...treatment,
        _treatmentId: treatmentId,
        _stats: stats,
        _contraNames: contraNames,
        _contraSet: contraSet,
        _priceNumber: priceNumber,
        _priceFormatted: priceFormatted,
        _riskNumber: toNumber(riskNumber),
        _riskFormatted: riskFormatted,
        _effectMinMinutes: effectMin,
        _effectMaxMinutes: effectMax,
      };
    }

    return out;
  }, [treatmentsBaseRaw, statsByTreatmentId, riskMaxById]);

  const contraindicationOptions = useMemo(() => {
    const map = new Map();

    for (let i = 0; i < treatmentsBase.length; i++) {
      const treatment = treatmentsBase[i];
      const names = treatment?._contraNames || [];

      for (let j = 0; j < names.length; j++) {
        const name = names[j];
        const key = normalizeKey(name);

        if (key && !map.has(key)) map.set(key, name);
      }
    }

    return Array.from(map.values()).sort((a, b) => a.localeCompare(b, 'en-US'));
  }, [treatmentsBase]);

  const applyFilters = useCallback(
    (nextFilters = filters, opts = {}) => {
      const safe = enforceMandatoryFilters(nextFilters);

      if (opts.reset) setHighlightSortField(false);
      else setHighlightSortField(true);

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
    const safe = enforceMandatoryFilters(deferredAppliedFilters);

    const selectedContraindications = (safe.contraindications || [])
      .map(normalizeKey)
      .filter(Boolean);

    const group = safe.group;

    return (treatmentsBase || []).filter((treatment) => {
      if (!treatment?._treatmentId) return false;
      if (!treatment?._stats) return false;

      if (!isIndicatedForGroup(treatment, group)) return false;

      if (selectedContraindications.length > 0) {
        const set = treatment._contraSet;

        for (let i = 0; i < selectedContraindications.length; i++) {
          if (set.has(selectedContraindications[i])) return false;
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
    const safe = enforceMandatoryFilters(deferredAppliedFilters);
    const arr = [...filteredTreatments];

    const criterion = safe.sortBy || 'efficacy';
    const order = safe.sortOrder || 'desc';
    const direction = order === 'asc' ? 1 : -1;

    if (criterion === 'none') return arr;

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

    arr.sort((a, b) => (getValue(a) - getValue(b)) * direction);

    return arr;
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
      <div className="tratamentos-error-container">
        <div className="tratamentos-error-box">
          <h2>Oops!</h2>
          <p>{bootError}</p>
          <button
            className="tratamentos-error-button"
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
      <div className="tratamentos-loader-container">
        <div className="tratamentos-loader-spinner" />
        <p className="tratamentos-loader-text"></p>
      </div>
    );
  }

  const visualCriterion = filters.sortBy;

  return (
    <div className="tratamentos-page tratamentos-dinamicos-page">
      <div id="top" />

      <HeaderEnFilters summary={summary} />

      <main className="tratamentos-layout" ref={layoutRef}>
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

        <section className="conteudo">
          <div className="tratamentos-list">
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
                      slugifyEF(EFFICACY_LABEL)
                    )}`}
                    className="tratamento-card"
                    style={{ textDecoration: 'none' }}
                  >
                    <div className="tratamento-content">
                      <div className="tratamento-imagem">
                        <img
                          src={treatment.image || '/default-image.jpg'}
                          alt={treatment.name || 'Image not available'}
                          className="img-fluid"
                          loading="lazy"
                          decoding="async"
                          fetchPriority={index < 2 ? 'high' : 'auto'}
                        />
                      </div>

                      <div className="tratamento-info">
                        <h3>{treatment.name}</h3>

                        {Array.isArray(treatment.treatment_type) &&
                          treatment.treatment_type.length > 0 && (
                            <p className="tipo-tratamento">
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
                          <strong>Manufacturer:</strong>{' '}
                          {treatment.manufacturer || 'ND'}
                        </p>

                        <div
                          className="btn mt-2 tratamento-details-btn"
                          style={detailsBtnStyle}
                        >
                          view details <span style={{ fontWeight: 'bold' }}>&#8250;</span>
                        </div>

                        <p>{treatment.description_for_list || treatment.description}</p>
                      </div>

                      <div className="eficacia-container">
                        <p className="eficacia-title">
                        <span className="eficacia-label">Efficacy:</span>{' '}
                        <span className="eficacia-sub">{EFFICACY_LABEL}</span>
                        </p>

                        <div className="eficacia-bar-container">
                          <div
                            className="efficacy-filled"
                            style={{ width: `${widthBar}%` }}
                          />
                          <div
                            className="efficacy-marker"
                            style={{ left: `calc(${widthBar}% - 7px)` }}
                          />
                        </div>

                        <p className="eficacia-range">
                          <span className="eficacia-min">
                            {efficacyMin !== null
                              ? `${String(efficacyMin.toFixed(2)).replace('.', ',')} to`
                              : 'ND to'}
                          </span>

                          <span className="eficacia-max">
                            {' '}
                            {efficacyMax !== null
                              ? `${String(efficacyMax.toFixed(2)).replace('.', ',')}%`
                              : 'ND%'}
                          </span>
                        </p>

                        <div
                          className={`campo-variavel ${
                            visualCriterion === 'cost'
                              ? 'campo-variavel--inline'
                              : 'campo-variavel--stack'
                          } ${highlightSortField ? 'campo-variavel--highlight' : ''}`}
                        >
                          {visualCriterion === 'cost' ? (
                            <div className="prazo-container">
                              <p className="prazo-title">Price:</p>
                              <p className="prazo-value">{treatment._priceFormatted}</p>
                            </div>
                          ) : visualCriterion === 'risk' ? (
                            <>
                              <p className="prazo-title">Risk of adverse reaction:</p>
                              <p className="prazo-value">{treatment._riskFormatted}</p>
                            </>
                          ) : (
                            <>
                              <p className="prazo-title">Time to effect:</p>
                              <p className="prazo-value">
                                {formatEffectTime(treatment)}
                              </p>
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
              <div className="tratamentos-load-more-wrap">
                <button
                  type="button"
                  onClick={() => setVisibleCount((value) => value + PAGE_SIZE)}
                  className="tratamentos-load-more-btn"
                >
                  Load more
                </button>
              </div>
            )}

            {showBackToTop && (
              <button
                type="button"
                onClick={scrollToTop}
                className="tratamentos-back-to-top"
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