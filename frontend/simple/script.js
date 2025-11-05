const API_BASE = 'http://localhost:8000/api/v1';

const endpointSelect = document.getElementById('endpoint');
const searchInput = document.getElementById('search');
const regionFilter = document.getElementById('regionFilter');
const typeFilter = document.getElementById('typeFilter');
const fetchBtn = document.getElementById('fetchBtn');
const outputEl = document.getElementById('output');
const statsEl = document.getElementById('stats');
const statusEl = document.getElementById('status');

// Location codes controls
const lcLat = document.getElementById('lcLat');
const lcLon = document.getElementById('lcLon');
const lcCode = document.getElementById('lcCode');
const lcGenBtn = document.getElementById('lcGenBtn');
const lcResolveBtn = document.getElementById('lcResolveBtn');

// Map init
const map = L.map('map').setView([5.5, 46.2], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let geoLayer = null;
let clusterLayer = null;

function clearMap() {
  if (geoLayer) {
    map.removeLayer(geoLayer);
    geoLayer = null;
  }
  if (clusterLayer) {
    map.removeLayer(clusterLayer);
    clusterLayer = null;
  }
}

function fitIfPossible(layer) {
  try {
    map.fitBounds(layer.getBounds(), { padding: [10, 10] });
  } catch (_) {
    // ignore
  }
}

function toFeatureCollection(data, resource) {
  // If already GeoJSON FeatureCollection
  if (data && data.type === 'FeatureCollection') return data;

  // Otherwise, convert known schemas to GeoJSON
  // Expected: { data: [...], count: N }
  const items = Array.isArray(data?.data) ? data.data : [];

  // Regions/Districts/Roads via format=geojson will already be FC, so above branch captures that.
  // For points (airports/ports/checkpoints): build Point features from lat/lon
  const features = items
    .map((it) => {
      // Airports/ports/checkpoints likely have latitude/longitude
      const lat = it.latitude ?? it.lat ?? it.centroid?.lat;
      const lon = it.longitude ?? it.lon ?? it.centroid?.lon;
      if (typeof lat !== 'number' || typeof lon !== 'number') return null;
      return {
        type: 'Feature',
        properties: { ...it },
        geometry: { type: 'Point', coordinates: [lon, lat] }
      };
    })
    .filter(Boolean);

  return { type: 'FeatureCollection', features };
}

function buildUrl(resource, query) {
  const params = new URLSearchParams();
  const search = (searchInput.value || '').trim();
  const region = (regionFilter.value || '').trim();
  const type = (typeFilter.value || '').trim();

  if (resource === 'regions' || resource === 'districts' || resource === 'roads') {
    // Ask API to return GeoJSON for these
    params.set('format', 'geojson');
  }

  if (resource === 'districts' && search) {
    // API supports region filter by exact name
    params.set('region', search);
  }
  if (resource === 'districts' && region) {
    params.set('region', region);
  }

  if (resource === 'roads' && search) {
    // No district spatial yet; search matches road name contains
    params.set('district', search);
  }
  if (resource === 'roads' && type) {
    params.set('type', type);
  }
  if (resource === 'airports' && type) {
    params.set('type', type);
  }

  // Fallback limit for sanity
  if (!params.has('limit')) params.set('limit', '100');

  // Map resource to real path
  const pathMap = {
    regions: `${API_BASE}/regions`,
    districts: `${API_BASE}/districts`,
    roads: `${API_BASE}/roads`,
    airports: `${API_BASE}/transport/airports`,
    ports: `${API_BASE}/transport/ports`,
    checkpoints: `${API_BASE}/transport/checkpoints`,
  };

  const base = pathMap[resource] || `${API_BASE}/regions`;
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

async function fetchData() {
  const resource = endpointSelect.value;
  const url = buildUrl(resource);
  statsEl.textContent = '';
  statusEl.textContent = `Loading...`;
  outputEl.textContent = '';
  clearMap();

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const json = await res.json();

    // Show JSON
    outputEl.textContent = JSON.stringify(json, null, 2);

    // Convert to FeatureCollection if needed
    const fc = toFeatureCollection(json, resource);
    if (fc && Array.isArray(fc.features) && fc.features.length) {
      if (resource === 'airports' || resource === 'ports' || resource === 'checkpoints') {
        clusterLayer = L.markerClusterGroup();
        fc.features.forEach(ft => {
          if (ft.geometry && ft.geometry.type === 'Point') {
            const [lon, lat] = ft.geometry.coordinates;
            const props = ft.properties || {};
            const name = props.name || 'Unnamed';
            const marker = L.marker([lat, lon]);
            marker.bindPopup(`<b>${name}</b><br/><small>${Object.keys(props).slice(0,8).map(k=>`${k}: ${props[k]}`).join('<br/>')}</small>`);
            clusterLayer.addLayer(marker);
          }
        });
        clusterLayer.addTo(map);
        try { map.fitBounds(clusterLayer.getBounds(), { padding: [10,10] }); } catch(_){}
      } else {
        geoLayer = L.geoJSON(fc, {
          style: feature => ({
            color: resource === 'roads' ? '#0ea5e9' : '#10b981',
            weight: resource === 'roads' ? 2 : 1,
            fillOpacity: resource === 'regions' || resource === 'districts' ? 0.2 : 0.6,
          }),
          onEachFeature: (feature, layer) => {
            const props = feature.properties || {};
            const name = props.name || props.title || 'Unnamed';
            layer.bindPopup(`<b>${name}</b><br/>` +
              `<small>${Object.keys(props).slice(0, 8).map(k => `${k}: ${props[k]}`).join('<br/>')}</small>`);
          }
        }).addTo(map);
        fitIfPossible(geoLayer);
      }
      statsEl.textContent = `Features: ${fc.features.length}`;
    } else {
      statsEl.textContent = 'No features found.';
    }
    statusEl.textContent = '';
  } catch (err) {
    statsEl.textContent = '';
    statusEl.textContent = `Error: ${err.message}`;
    outputEl.textContent = String(err);
  }
}

fetchBtn.addEventListener('click', fetchData);

// Populate regions for filter and wire endpoint-dependent controls
async function loadRegionsForFilter() {
  try {
    const res = await fetch(`${API_BASE}/regions?limit=300`);
    const body = await res.json();
    const items = Array.isArray(body?.data) ? body.data : [];
    for (const r of items) {
      const opt = document.createElement('option');
      opt.value = r.name;
      opt.textContent = r.name;
      regionFilter.appendChild(opt);
    }
  } catch (_) {}
}

function refreshFilterControls() {
  const resource = endpointSelect.value;
  // Reset
  regionFilter.classList.add('hidden');
  typeFilter.classList.add('hidden');
  // Configure type options
  typeFilter.innerHTML = '<option value="">All types</option>';
  if (resource === 'districts') {
    regionFilter.classList.remove('hidden');
  } else if (resource === 'roads') {
    typeFilter.classList.remove('hidden');
    ['primary','secondary'].forEach(t=>{
      const o=document.createElement('option'); o.value=t; o.textContent=t; typeFilter.appendChild(o);
    });
  } else if (resource === 'airports') {
    typeFilter.classList.remove('hidden');
    ['international','domestic'].forEach(t=>{
      const o=document.createElement('option'); o.value=t; o.textContent=t; typeFilter.appendChild(o);
    });
  }
}

endpointSelect.addEventListener('change', refreshFilterControls);

// Location code handlers
lcGenBtn.addEventListener('click', async () => {
  const lat = parseFloat(lcLat.value);
  const lon = parseFloat(lcLon.value);
  if (Number.isNaN(lat) || Number.isNaN(lon)) {
    statusEl.textContent = 'Enter valid lat/lon';
    return;
  }
  statusEl.textContent = 'Generating code...';
  try {
    const res = await fetch(`${API_BASE}/locationcode/generate?lat=${lat}&lon=${lon}`);
    const data = await res.json();
    lcCode.value = data.code || '';
    outputEl.textContent = JSON.stringify(data, null, 2);
    statusEl.textContent = '';
  } catch (e) {
    statusEl.textContent = 'Failed to generate code';
  }
});

lcResolveBtn.addEventListener('click', async () => {
  const code = (lcCode.value || '').trim();
  if (!code) {
    statusEl.textContent = 'Enter a PlusCode';
    return;
  }
  statusEl.textContent = 'Resolving code...';
  try {
    const res = await fetch(`${API_BASE}/locationcode/resolve?code=${encodeURIComponent(code)}`);
    const data = await res.json();
    outputEl.textContent = JSON.stringify(data, null, 2);
    if (typeof data.latitude_center === 'number' && typeof data.longitude_center === 'number') {
      map.setView([data.latitude_center, data.longitude_center], 12);
    }
    statusEl.textContent = '';
  } catch (e) {
    statusEl.textContent = 'Failed to resolve code';
  }
});

// Init
loadRegionsForFilter().then(refreshFilterControls);


