<script> 
	import { api } from '$lib/api'; 
	import { onMount } from 'svelte'; 
	import { goto } from '$app/navigation';
 
	let user = null; 
	let error = ''; 
	let loading = true;
 
	onMount(async () => { 
		const token = localStorage.getItem('token'); 
		if (!token) { 
			goto('/login'); 
			return; 
		}
 
		try { 
			const res = await api('/auth/me', { 
				headers: { Authorization: `Bearer ${token}` } 
			}); 
			user = res; 
		} catch (err) { 
			error = err.message; 
			// If token is invalid, redirect to login 
			if (err.message.includes('401') || err.message.includes('unauthorized')) { 
				localStorage.removeItem('token'); 
				goto('/login'); 
			} 
		} finally { 
			loading = false; 
		} 
	});
 
	function logout() { 
		localStorage.removeItem('token'); 
		goto('/login'); 
	} 
</script>
 
<div style="min-height: 100vh; display: flex; align-items: center; justify-content: center; background-color: #f9fafb;"> 
	<div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: 100%; max-width: 28rem; text-align: center;"> 
		{#if loading} 
			<p>Loading profile...</p> 
			<div style="margin-top: 1rem;"> 
				<div style="width: 2rem; height: 2rem; border: 0.125rem solid #e5e7eb; border-top: 0.125rem solid #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto;"></div> 
			</div> 
		{:else if user} 
			<h2 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem;">Welcome!</h2> 
			<div style="margin-bottom: 1rem; text-align: left;"> 
				<div style="margin-bottom: 1rem;"> 
					<p><strong>Email:</strong> {user.email}</p> 
					<p><strong>User ID:</strong> {user.id}</p> 
					<p><strong>Role:</strong> <span style="color: {user.role === 'ADMIN' ? '#dc2626' : user.role === 'MAINTAINER' ? '#d97706' : '#059669'}; font-weight: 600;">{user.role}</span></p> 
					{#if user.oauth_provider} 
						<p><strong>Login Method:</strong> {user.oauth_provider}</p> 
					{:else} 
						<p><strong>Login Method:</strong> Email/Password</p> 
					{/if} 
				</div> 
				 
				<div style="border-top: 1px solid #e5e7eb; padding-top: 1rem;"> 
					<h3 style="font-size: 1.125rem; font-weight: 500; margin-bottom: 0.75rem;">Quick Actions</h3> 
					<div style="display: flex; flex-direction: column; gap: 0.5rem;"> 
						<a href="/issues" style="display: block; width: 100%; text-align: center; background-color: #2563eb; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; text-decoration: none;"> 
							{user.role === 'REPORTER' ? 'View My Issues' : 'View All Issues'} 
						</a> 
						<a href="/issues/create" style="display: block; width: 100%; text-align: center; background-color: #059669; color: white; padding: 0.5rem 1rem; border-radius: 0.375rem; text-decoration: none;"> 
							Create New Issue 
						</a> 
					</div> 
				</div> 
			</div> 
			<button class="btn-logout" on:click={logout}> 
				Logout 
			</button> 
		{:else if error} 
			<p style="color: #dc2626; margin-bottom: 1rem;">{error}</p> 
			<button style="background-color: #f3f4f6; color: #1f2937; padding: 0.5rem 1rem; border-radius: 0.375rem; border: none; cursor: pointer;" on:click={() => goto('/login')}> 
				Go to Login 
			</button> 
		{/if} 
	</div> 
</div>
 
<style> 
	.btn-logout { 
		background-color: #dc2626; 
		color: white; 
		padding: 0.5rem 1rem; 
		border-radius: 0.375rem; 
		border: none; 
		cursor: pointer; 
		width: 100%; 
		margin-top: 1.5rem; 
	} 
	.btn-logout:hover { 
		background-color: #b91c1c; 
	}
 
	@keyframes spin { 
		0% { transform: rotate(0deg); } 
		100% { transform: rotate(360deg); } 
	} 
</style>