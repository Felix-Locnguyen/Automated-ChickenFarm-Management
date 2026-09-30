const API_BASE = '/api';

export async function fetchFarmData() {
  const response = await fetch(`${API_BASE}/farm-data`);
  if (!response.ok) throw new Error('Failed to fetch farm data');
  return response.json();
}

export async function fetchCoops() {
  const response = await fetch(`${API_BASE}/coops`);
  if (!response.ok) throw new Error('Failed to fetch coops');
  return response.json();
}

export async function toggleDevice(coopId, deviceKey, state) {
  const response = await fetch(`${API_BASE}/coops/${coopId}/devices/${deviceKey}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state })
  });
  if (!response.ok) throw new Error('Failed to toggle device');
  return response.json();
}
