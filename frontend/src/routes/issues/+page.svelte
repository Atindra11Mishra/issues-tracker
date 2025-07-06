
<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';

	let issues = [];
	let loading = true;
	let error = '';
	let currentUser = null;

	onMount(async () => {
		await loadCurrentUser();
		await loadIssues();
	});

	async function loadCurrentUser() {
		const token = localStorage.getItem('token');
		if (!token) {
			goto('/login');
			return;
		}

		try {
			currentUser = await api('/auth/me', {
				headers: { Authorization: `Bearer ${token}` }
			});
		} catch (err) {
			console.error('Failed to load current user:', err);
		}
	}

	async function loadIssues() {
		const token = localStorage.getItem('token');
		if (!token) {
			goto('/login');
			return;
		}

		try {
			loading = true;
			const freshIssues = await api('/issues', {
				headers: { Authorization: `Bearer ${token}` }
			});
			issues = freshIssues;
			console.log('Loaded issues:', issues);
		} catch (err) {
			error = err.message;
			if (err.message.includes('401')) {
				localStorage.removeItem('token');
				goto('/login');
			}
		} finally {
			loading = false;
		}
	}

	async function advanceStatus(issueId) {
		const token = localStorage.getItem('token');
		try {
			console.log(`Advancing issue ${issueId}`);
			const response = await api(`/issues/${issueId}/advance`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${token}` }
			});
			
			console.log('Advance response:', response);
			
			// Reload the entire issues list to get fresh data
			await loadIssues();
			
		} catch (err) {
			console.error('Advance error:', err);
			if (err.message.includes('403')) {
				error = 'You do not have permission to advance issue status. Only Maintainers and Admins can do this.';
			} else {
				error = `Failed to advance status: ${err.message}`;
			}
		}
	}

	async function deleteIssue(issueId) {
		if (!confirm('Are you sure you want to delete this issue?')) return;
		
		const token = localStorage.getItem('token');
		try {
			await api(`/issues/${issueId}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});
			await loadIssues();
		} catch (err) {
			if (err.message.includes('403')) {
				error = 'You do not have permission to delete this issue.';
			} else {
				error = `Failed to delete issue: ${err.message}`;
			}
		}
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
	}

	// Check if arrow button should show
	function showAdvanceButton(issue) {
		// Only for maintainers and admins
		if (!currentUser || (currentUser.role !== 'MAINTAINER' && currentUser.role !== 'ADMIN')) {
			return false;
		}
		// Show for all statuses except DONE
		return issue.status !== 'DONE';
	}

	// Check if edit button should show (only admins)
	function showEditButton(issue) {
		return currentUser && currentUser.role === 'ADMIN';
	}

	// Check if delete button should show (only admins)
	function showDeleteButton(issue) {
		return currentUser && currentUser.role === 'ADMIN';
	}
</script>

<div style="min-height: 100vh; background-color: #f9fafb; padding: 2rem;">
	<div style="max-width: 1200px; margin: 0 auto;">
		<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
			<h1 style="font-size: 2rem; font-weight: bold; color: #111827;">
				{currentUser?.role === 'REPORTER' ? 'My Issues' : 'All Issues'}
			</h1>
			<div style="display: flex; gap: 1rem;">
				<a href="/issues/create" class="btn btn-primary">Create New Issue</a>
				<a href="/profile" class="btn btn-secondary">Back to Profile</a>
			</div>
		</div>

		{#if error}
			<div class="alert alert-error">
				{error}
			</div>
		{/if}

		{#if loading}
			<div style="text-align: center; padding: 2rem;">
				<div class="spinner"></div>
				<p style="margin-top: 1rem; color: #6b7280;">Loading issues...</p>
			</div>
		{:else if issues.length === 0}
			<div style="text-align: center; padding: 4rem;">
				<h3 style="margin-top: 0.5rem; font-weight: 500; color: #111827;">No issues</h3>
				<p style="margin-top: 0.25rem; color: #6b7280;">Get started by creating a new issue.</p>
				<div style="margin-top: 1.5rem;">
					<a href="/issues/create" class="btn btn-primary">Create New Issue</a>
				</div>
			</div>
		{:else}
			<div style="background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden;">
				{#each issues as issue, index}
					<div class="issue-item" style="padding: 1.5rem; {index !== issues.length - 1 ? 'border-bottom: 1px solid #e5e7eb;' : ''}">
						<div style="display: flex; justify-content: space-between; align-items: start;">
							<div style="flex: 1;">
								<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
									<h3 style="font-size: 1.125rem; font-weight: 500; color: #111827; margin: 0;">
										<a href="/issues/{issue.id}" style="text-decoration: none; color: inherit;">
											{issue.title}
										</a>
									</h3>
									<div style="display: flex; gap: 0.5rem;">
										<span class="badge badge-{issue.status.toLowerCase()}">{issue.status}</span>
										<span class="badge badge-{issue.severity.toLowerCase()}">{issue.severity}</span>
									</div>
								</div>
								<p style="margin: 0.5rem 0; color: #6b7280; font-size: 0.875rem;">
									{issue.description.substring(0, 150)}...
								</p>
								<div style="margin-top: 0.5rem; display: flex; align-items: center; font-size: 0.875rem; color: #9ca3af; flex-wrap: wrap; gap: 1rem;">
									<span>Created: {formatDate(issue.created_at)}</span>
									{#if currentUser?.role !== 'REPORTER'}
										<span>Creator ID: {issue.creator_id}</span>
									{/if}
									{#if issue.file_name}
										<span>📎 {issue.file_name}</span>
									{/if}
								</div>
							</div>
							<div style="margin-left: 1rem; display: flex; gap: 0.5rem;">
								<!-- Advance Status Button - Shows until DONE -->
								{#if showAdvanceButton(issue)}
									<button 
										on:click={() => advanceStatus(issue.id)}
										class="btn btn-sm btn-blue"
										title="Advance Status (Current: {issue.status})"
									>
										→
									</button>
								{/if}
								
								<!-- Edit button - only admins -->
								{#if showEditButton(issue)}
									<a href="/issues/{issue.id}/edit" class="btn btn-sm btn-secondary" title="Edit">
										✏️
									</a>
								{/if}
								
								<!-- Delete button - only admins -->
								{#if showDeleteButton(issue)}
									<button 
										on:click={() => deleteIssue(issue.id)}
										class="btn btn-sm btn-danger"
										title="Delete"
									>
										🗑️
									</button>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
		font-weight: 500;
		border-radius: 0.375rem;
		text-decoration: none;
		border: none;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-primary {
		background-color: #2563eb;
		color: white;
	}
	.btn-primary:hover {
		background-color: #1d4ed8;
	}

	.btn-secondary {
		background-color: white;
		color: #374151;
		border: 1px solid #d1d5db;
	}
	.btn-secondary:hover {
		background-color: #f9fafb;
	}

	.btn-blue {
		background-color: #2563eb;
		color: white;
	}
	.btn-blue:hover {
		background-color: #1d4ed8;
	}

	.btn-danger {
		background-color: #dc2626;
		color: white;
	}
	.btn-danger:hover {
		background-color: #b91c1c;
	}

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
	}

	.badge {
		display: inline-flex;
		align-items: center;
		padding: 0.25rem 0.625rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
	}

	.badge-open {
		background-color: #fee2e2;
		color: #dc2626;
	}

	.badge-triaged {
		background-color: #fef3c7;
		color: #d97706;
	}

	.badge-in_progress {
		background-color: #dbeafe;
		color: #2563eb;
	}

	.badge-done {
		background-color: #d1fae5;
		color: #059669;
	}

	.badge-low {
		background-color: #f3f4f6;
		color: #374151;
	}

	.badge-medium {
		background-color: #fed7aa;
		color: #ea580c;
	}

	.badge-high {
		background-color: #fee2e2;
		color: #dc2626;
	}

	.badge-critical {
		background-color: #ede9fe;
		color: #7c3aed;
	}

	.alert {
		padding: 1rem;
		border-radius: 0.375rem;
		margin-bottom: 1.5rem;
	}

	.alert-error {
		background-color: #fee2e2;
		border: 1px solid #fca5a5;
		color: #dc2626;
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 0.125rem solid #e5e7eb;
		border-top: 0.125rem solid #2563eb;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.issue-item:hover {
		background-color: #f9fafb;
	}
</style>