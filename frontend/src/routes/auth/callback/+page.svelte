<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let message = 'Processing Google login...';

	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const token = urlParams.get('token');
		const error = urlParams.get('error');
		
		if (token) {
			localStorage.setItem('token', token);
			message = 'Login successful! Redirecting...';
			setTimeout(() => {
				goto('/profile');
			}, 1000);
		} else if (error) {
			message = 'Google login failed. Redirecting to login page...';
			setTimeout(() => {
				goto('/login?error=oauth_failed');
			}, 3000);
		} else {
			message = 'No authentication data received. Redirecting...';
			setTimeout(() => {
				goto('/login');
			}, 3000);
		}
	});
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-100">
	<div class="bg-white p-6 rounded shadow-md w-full max-w-md text-center">
		<h2 class="text-xl font-semibold mb-4">Google OAuth</h2>
		<div class="mb-4">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
		</div>
		<p>{message}</p>
	</div>
</div>