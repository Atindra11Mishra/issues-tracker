<script>
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';

	let email = '';
	let password = '';
	let confirmPassword = '';
	let message = '';
	let loading = false;

	async function signup() {
		if (!email || !password || !confirmPassword) {
			message = 'Please fill in all fields';
			return;
		}

		if (password !== confirmPassword) {
			message = 'Passwords do not match';
			return;
		}

		if (password.length < 6) {
			message = 'Password must be at least 6 characters long';
			return;
		}

		loading = true;
		message = '';

		try {
			const res = await api('/auth/signup', {
				method: 'POST',
				body: JSON.stringify({ email, password })
			});
			
			localStorage.setItem('token', res.access_token);
			goto('/profile');
		} catch (err) {
			message = err.message;
		} finally {
			loading = false;
		}
	}

	function signupWithGoogle() {
		// Redirect to Google OAuth
		window.location.href = 'http://localhost:8000/oauth/google';
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-100">
	<div class="bg-white p-6 rounded shadow-md w-full max-w-md">
		<h2 class="text-2xl font-semibold mb-4">Sign Up</h2>
		<form on:submit|preventDefault={signup} class="space-y-4">
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
			<input 
				type="password" 
				bind:value={confirmPassword} 
				placeholder="Confirm Password" 
				required 
				class="input" 
				disabled={loading}
			/>
			<button 
				type="submit" 
				class="btn-primary w-full" 
				disabled={loading}
			>
				{loading ? 'Creating Account...' : 'Create Account'}
			</button>
		</form>
		
		<div class="my-4 text-center text-gray-500">
			<span class="px-2 bg-white">or</span>
		</div>
		
		<a 
			href="http://localhost:8000/oauth/google" 
			class="btn-google w-full block text-center"
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
			Already have an account? <a href="/login" class="text-blue-600">Login</a>
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
		background-color: #16a34a;
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