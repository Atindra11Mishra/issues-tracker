<script>
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	let email = '';
	let password = '';
	let message = '';
	let loading = false;

	onMount(() => {
		// Check for OAuth error
		const urlParams = new URLSearchParams(window.location.search);
		const error = urlParams.get('error');
		if (error === 'oauth_failed') {
			message = 'Google login failed. Please try again or use email/password.';
		}
	});

	async function login() {
		if (!email || !password) {
			message = 'Please fill in all fields';
			return;
		}

		loading = true;
		message = '';

		try {
			const formData = new FormData();
			formData.append('username', email); // OAuth2PasswordRequestForm expects 'username'
			formData.append('password', password);

			const res = await fetch('http://localhost:8000/auth/login', {
				method: 'POST',
				body: formData
			});

			if (!res.ok) {
				const errorData = await res.json();
				throw new Error(errorData.detail || 'Login failed');
			}

			const data = await res.json();
			localStorage.setItem('token', data.access_token);
			goto('/profile');
		} catch (err) {
			message = err.message;
		} finally {
			loading = false;
		}
	}

	function loginWithGoogle() {
		// Redirect to Google OAuth
		window.location.href = 'http://localhost:8000/oauth/google';
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-100">
	<div class="bg-white p-6 rounded shadow-md w-full max-w-md">
		<h2 class="text-2xl font-semibold mb-4">Login</h2>
		<form on:submit|preventDefault={login} class="space-y-4">
			<input 
				type="email" 
				bind:value={email} 
				placeholder="Email" 
				required 
				class="input" 
				disabled={loading}
			/>
			<input 
				type="password" 
				bind:value={password} 
				placeholder="Password" 
				required 
				class="input" 
				disabled={loading}
			/>
			<button 
				type="submit" 
				class="btn-primary w-full" 
				disabled={loading}
			>
				{loading ? 'Logging in...' : 'Login'}
			</button>
		</form>
		<a 
			href="http://localhost:8000/oauth/google" 
			class="btn-google w-full block text-center mt-4"
		>
			<svg class="w-5 h-5 inline mr-2" viewBox="0 0 24 24">
				<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
				<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
				<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
				<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
			</svg>
			Continue with Google
		</a>
		<p class="text-sm text-gray-500 mt-4">
			Don't have an account? <a href="/signup" class="text-blue-600">Sign up</a>
		</p>
		{#if message}
			<p class="text-red-600 mt-2">{message}</p>
		{/if}
	</div>
</div>

<style>
	.input {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 0.375rem;
	}
	.input:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.btn-primary {
		background-color: #2563eb;
		color: white;
		padding: 0.5rem;
		border-radius: 0.375rem;
	}
	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.btn-google {
		background-color: #ffffff;
		color: #757575;
		border: 1px solid #dadce0;
		padding: 0.75rem;
		border-radius: 0.375rem;
		text-decoration: none;
		font-weight: 500;
		transition: all 0.2s;
	}
	.btn-google:hover {
		background-color: #f8f9fa;
		box-shadow: 0 1px 3px rgba(0,0,0,0.1);
	}
</style>