export const API_BASE = 'http://localhost:8000';

export async function api(endpoint, options = {}) {
	console.log(`Making API request to: ${API_BASE}${endpoint}`);
	console.log('Request options:', options);
	
	try {
		const res = await fetch(`${API_BASE}${endpoint}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...(options.headers || {})
			},
			credentials: 'include'
		});
		
		console.log('Response status:', res.status);
		console.log('Response headers:', res.headers);
		
		if (!res.ok) {
			const errorText = await res.text();
			console.error('API Error:', errorText);
			throw new Error(errorText);
		}
		
		return res.json();
	} catch (error) {
		console.error('Fetch error:', error);
		throw error;
	}
}