/**
 * WKO5 Dashboard — API Client
 *
 * Plain-browser JS (no bundler). Attaches to window.WKO5API.
 * Base URL is configurable for Electron wrapping via window.__WKO5_CONFIG__.apiBase.
 */

/**
 * @class WKO5API
 * @description HTTP client for the WKO5 FastAPI backend.
 *              Handles auth, connection tracking, and typed endpoint helpers.
 */
class WKO5API {
  /**
   * @param {string} [baseUrl] - API origin. Falls back to config global, then current origin.
   * @param {string} [token]   - Bearer token. Falls back to URL ?token= param, then localStorage.
   */
  constructor(baseUrl, token) {
    this.baseUrl = (
      baseUrl ||
      (window.__WKO5_CONFIG__ && window.__WKO5_CONFIG__.apiBase) ||
      window.location.origin
    ).replace(/\/+$/, '');

    this.token = token || this._resolveToken();
    this.connected = false;

    /** @private */
    this._eventTarget = new EventTarget();
  }

  /* ------------------------------------------------------------------
   *  Token helpers
   * ----------------------------------------------------------------*/

  /**
   * Resolve a token from the URL search params or localStorage.
   * @private
   * @returns {string|null}
   */
  _resolveToken() {
    try {
      var params = new URLSearchParams(window.location.search);
      var urlToken = params.get('token');
      if (urlToken) {
        localStorage.setItem('wko5_token', urlToken);
        // Strip token from URL for security (prevents Referer leak)
        if (window.history && window.history.replaceState) {
          var url = new URL(window.location);
          url.searchParams.delete('token');
          window.history.replaceState({}, '', url);
        }
        return urlToken;
      }
    } catch (_) {
      /* URL parsing may fail in non-browser contexts */
    }

    try {
      return localStorage.getItem('wko5_token');
    } catch (_) {
      return null;
    }
  }

  /**
   * Persist a bearer token in memory and localStorage.
   * @param {string} token
   */
  setToken(token) {
    this.token = token;
    try {
      localStorage.setItem('wko5_token', token);
    } catch (_) {
      /* localStorage may be unavailable */
    }
  }

  /* ------------------------------------------------------------------
   *  Connection status
   * ----------------------------------------------------------------*/

  /**
   * Update connection state and fire event when it changes.
   * @private
   * @param {boolean} status
   */
  _setConnected(status) {
    var previous = this.connected;
    this.connected = status;
    if (previous !== status) {
      this._eventTarget.dispatchEvent(
        new CustomEvent('connection-change', { detail: { connected: status } })
      );
    }
  }

  /**
   * Subscribe to API client events (e.g. 'connection-change').
   * @param {string} event
   * @param {Function} callback
   */
  on(event, callback) {
    this._eventTarget.addEventListener(event, callback);
  }

  /**
   * Unsubscribe from API client events.
   * @param {string} event
   * @param {Function} callback
   */
  off(event, callback) {
    this._eventTarget.removeEventListener(event, callback);
  }

  /* ------------------------------------------------------------------
   *  Core fetch
   * ----------------------------------------------------------------*/

  /**
   * Generic fetch wrapper with auth, JSON handling, and connection tracking.
   * @private
   * @param {string} path     - API path (e.g. '/api/health')
   * @param {RequestInit} [options]
   * @returns {Promise<any>} Parsed JSON response body.
   * @throws {Error} On non-2xx status with message including status code and body.
   */
  async _fetch(path, options) {
    var url = this.baseUrl + '/api' + path;

    var headers = {
      'Content-Type': 'application/json'
    };

    if (this.token) {
      headers['Authorization'] = 'Bearer ' + this.token;
    }

    var fetchOptions = Object.assign({}, options, {
      headers: Object.assign(headers, options && options.headers)
    });

    var response;
    try {
      response = await fetch(url, fetchOptions);
    } catch (err) {
      this._setConnected(false);
      throw new Error('Network error: ' + err.message);
    }

    if (response.ok) {
      this._setConnected(true);
      /* Some endpoints may return 204 No Content */
      var text = await response.text();
      return text ? JSON.parse(text) : null;
    }

    /* Non-2xx — still "connected" to the server, just an app-level error */
    this._setConnected(true);
    var body;
    try {
      body = await response.text();
    } catch (_) {
      body = '';
    }
    throw new Error('API ' + response.status + ': ' + body);
  }

  /* ------------------------------------------------------------------
   *  Query-string helper
   * ----------------------------------------------------------------*/

  /**
   * Build a query string from an object, omitting null/undefined values.
   * @private
   * @param {Object} params
   * @returns {string} e.g. '?limit=20&offset=0' or '' if empty
   */
  _qs(params) {
    var parts = [];
    for (var key in params) {
      if (params.hasOwnProperty(key) && params[key] != null) {
        parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
      }
    }
    return parts.length ? '?' + parts.join('&') : '';
  }

  /* ------------------------------------------------------------------
   *  GET endpoints
   * ----------------------------------------------------------------*/

  /** @returns {Promise<{status: string, cache_warm: boolean}>} */
  async getHealth() { return this._fetch('/health'); }

  /** @returns {Promise<{running: boolean, done: boolean, results: Object, errors: Object}>} */
  async getWarmupStatus() { return this._fetch('/warmup-status'); }

  /** @returns {Promise<Object>} Fitness / PMC data */
  async getFitness() { return this._fetch('/fitness'); }

  /** @returns {Promise<Object[]>} Full PMC history [{date, TSS, CTL, ATL, TSB}, ...] */
  async getPmc(params) { return this._fetch('/pmc' + this._qs(params || {})); }

  /**
   * @param {Object} [params]
   * @param {number} [params.limit]
   * @param {number} [params.offset]
   * @returns {Promise<Object[]>}
   */
  async getActivities(params) { return this._fetch('/activities' + this._qs(params || {})); }

  /**
   * @param {Object} [params]
   * @param {number} [params.days]
   * @returns {Promise<Object>}
   */
  async getModel(params) { return this._fetch('/model' + this._qs(params || {})); }

  /** @returns {Promise<Object>} Athlete profile */
  async getProfile() { return this._fetch('/profile'); }

  /**
   * @param {string|number} id - Ride / activity ID
   * @returns {Promise<Object>}
   */
  async getRide(id) { return this._fetch('/ride/' + encodeURIComponent(id)); }

  /** @param {string|number} id */
  async getRideIntervals(id) { return this._fetch('/ride/' + encodeURIComponent(id) + '/intervals'); }

  /** @param {string|number} id */
  async getRideEfforts(id) { return this._fetch('/ride/' + encodeURIComponent(id) + '/efforts'); }

  /** @returns {Promise<Object>} Rolling FTP history */
  async getRollingFtp() { return this._fetch('/rolling-ftp'); }

  /** @param {string|number} id */
  async getSegments(id) { return this._fetch('/segments/' + encodeURIComponent(id)); }

  /** @returns {Promise<Object>} Durability metrics */
  async getDurability() { return this._fetch('/durability'); }

  /** @param {string|number} id */
  async getDemand(id) { return this._fetch('/demand/' + encodeURIComponent(id)); }

  /** @param {string|number} id */
  async getGapAnalysis(id) { return this._fetch('/gap-analysis/' + encodeURIComponent(id)); }

  /** @returns {Promise<Object>} Clinical flag alerts */
  async getClinicalFlags() { return this._fetch('/clinical-flags'); }

  /** @returns {Promise<Object[]>} Training block summaries */
  async getTrainingBlocks() { return this._fetch('/training-blocks'); }

  /** @returns {Promise<Object>} Weekly training summary */
  async getWeeklySummary() { return this._fetch('/weekly-summary'); }

  /** @returns {Promise<Object>} Current training phase detection */
  async getDetectPhase() { return this._fetch('/detect-phase'); }

  /** @returns {Promise<Object>} CTL target feasibility */
  async getFeasibility() { return this._fetch('/feasibility'); }

  /** @returns {Promise<Object[]>} Saved routes */
  async getRoutes() { return this._fetch('/routes'); }

  /** @param {string|number} id */
  async getRoute(id) { return this._fetch('/routes/' + encodeURIComponent(id)); }

  /** @returns {Promise<Object>} Bayesian posterior summary */
  async getPosteriorSummary() { return this._fetch('/posterior-summary'); }

  /** @returns {Promise<Object>} Server config */
  async getConfig() { return this._fetch('/config'); }

  /* ------------------------------------------------------------------
   *  POST endpoints
   * ----------------------------------------------------------------*/

  /**
   * Plan a ride (nutrition, pacing, demand).
   * @param {Object} data - Ride plan parameters
   * @returns {Promise<Object>}
   */
  async planRide(data) {
    return this._fetch('/plan-ride', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  /**
   * Trigger a model update on the server.
   * @returns {Promise<Object>}
   */
  async updateModels() {
    return this._fetch('/update-models', { method: 'POST' });
  }

  /* ------------------------------------------------------------------
   *  P3 endpoints
   * ----------------------------------------------------------------*/

  /** @returns {Promise<Object>} IF distribution histogram */
  async getIFDistribution() { return this._fetch('/if-distribution'); }

  /** @returns {Promise<Object>} FTP growth curve model */
  async getFTPGrowth() { return this._fetch('/ftp-growth'); }

  /** @returns {Promise<Object>} Day-to-day performance trend */
  async getPerformanceTrend() { return this._fetch('/performance-trend'); }

  /** @param {number} routeId */
  async getOpportunityCost(routeId) { return this._fetch('/opportunity-cost/' + encodeURIComponent(routeId)); }

  /** @param {Object} body - Glycogen budget parameters */
  async postGlycogenBudget(body) {
    return this._fetch('/glycogen-budget', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /** @returns {Promise<Object>} Rolling PD profile over time */
  async getRollingPDProfile() { return this._fetch('/rolling-pd-profile'); }

  /** @returns {Promise<Object>} Fresh baseline staleness */
  async getFreshBaseline() { return this._fetch('/fresh-baseline'); }

  /** @returns {Promise<Object>} Short power consistency */
  async getShortPowerConsistency() { return this._fetch('/short-power-consistency'); }
}

/* Expose globally — no module bundler */
window.WKO5API = WKO5API;
