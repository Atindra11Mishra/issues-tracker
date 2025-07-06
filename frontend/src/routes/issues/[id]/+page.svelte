<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api } from '$lib/api';

	let issue = null;
	let currentUser = null;
	let loading = true;
	let error = '';
	let advancing = false;

	const statusWorkflow = {
		OPEN: 'TRIAGED',
		TRIAGED: 'IN_PROGRESS',
		IN_PROGRESS: 'DONE',
		DONE: null
	};

	onMount(async () => {
		const issueId = $page.params.id;
		await loadIssue(issueId);
		await loadCurrentUser();
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
			console.error('Failed to load user:', err);
		}
	}

	async function loadIssue(issueId) {
		const token = localStorage.getItem('token');
		if (!token) {
			goto('/login');
			return;
		}

		try {
			loading = true;
			issue = await api(`/issues/${issueId}`, {
				headers: { Authorization: `Bearer ${token}` }
			});
		} catch (err) {
			error = err.message;
			if (err.message.includes('404')) {
				error = 'Issue not found or you do not have permission to view it.';
			} else if (err.message.includes('401')) {
				localStorage.removeItem('token');
				goto('/login');
			}
		} finally {
			loading = false;
		}
	}

	async function advanceStatus() {
		if (!issue) return;
		
		advancing = true;
		const token = localStorage.getItem('token');
		
		try {
			await api(`/issues/${issue.id}/advance`, {
				method: 'POST',
				headers: { Authorization: `Bearer ${token}` }
			});
			await loadIssue(issue.id);
		} catch (err) {
			error = `Failed to advance status: ${err.message}`;
		} finally {
			advancing = false;
		}
	}

	async function deleteIssue() {
		if (!issue || !confirm('Are you sure you want to delete this issue?')) return;
		
		const token = localStorage.getItem('token');
		try {
			await api(`/issues/${issue.id}`, {
				method: 'DELETE',
				headers: { Authorization: `Bearer ${token}` }
			});
			goto('/issues');
		} catch (err) {
			error = `Failed to delete issue: ${err.message}`;
		}
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
	}

	function markdownToHtml(markdown) {
		if (!markdown) return '';
		return markdown
			.replace(/### (.*$)/gim, '<h3 style="font-size: 1.125rem; font-weight: 600; margin: 1.5rem 0 0.75rem 0;">$1</h3>')
			.replace(/## (.*$)/gim, '<h2 style="font-size: 1.25rem; font-weight: 600; margin: 1.5rem 0 0.75rem 0;">$1</h2>')
			.replace(/# (.*$)/gim, '<h1 style="font-size: 1.5rem; font-weight: 700; margin: 1.5rem 0 0.75rem 0;">$1</h1>')
			.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
			.replace(/\*(.*?)\*/gim, '<em>$1</em>')
			.replace(/`(.*?)`/gim, '<code style="background-color: #f3f4f6; padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-size: 0.875rem;">$1</code>')
			.replace(/^\- (.*$)/gim, '<li style="margin-left: 1rem;">$1</li>')
			.replace(/\n\n/gim, '</p><p style="margin-bottom: 1rem;">')
			.replace(/\n/gim, '<br>')
			.replace(/^(.*)$/gim, '<p style="margin-bottom: 1rem;">$1</p>');
	}

	function downloadFile() {
		if (!issue || !issue.file_name) return;
		const token = localStorage.getItem('token');
		
		fetch(`http://localhost:8000/issues/${issue.id}/file`, {
			headers: { Authorization: `Bearer ${token}` }
		})
		.then(response => response.blob())
		.then(blob => {
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;
			link.download = issue.file_name;
			link.click();
			window.URL.revokeObjectURL(url);
		})
		.catch(err => {
			error = `Failed to download file: ${err.message}`;
		});
	}

	// Check if user can edit (REPORTERS: only their own issues, others can edit any)
	$: canEdit = currentUser && issue && (
		currentUser.role !== 'REPORTER' || 
		(currentUser.role === 'REPORTER' && issue.creator_id === currentUser.id)
	);

	// Check if user can advance status (only maintainers and admins, and not DONE)
	$: canAdvanceStatus = currentUser && ['MAINTAINER', 'ADMIN'].includes(currentUser.role) && issue && issue.status !== 'DONE' && statusWorkflow[issue.status];

	// Check if user can delete (ONLY ADMINS can delete any, REPORTERS only their own)
	$: canDelete = currentUser && issue && (
		currentUser.role === 'ADMIN' || 
		(currentUser.role === 'REPORTER' && issue.creator_id === currentUser.id)
	);
</script>

<div style="min-height: 100vh; background-color: #f9fafb; padding: 2rem;">
	<div style="max-width: 1000px; margin: 0 auto;">
		{#if loading}
			<div style="text-align: center; padding: 2rem;">
				<div class="spinner"></div>
				<p style="margin-top: 1rem; color: #6b7280;">Loading issue...</p>
			</div>
		{:else if error}
			<div class="alert alert-error">
				{error}
			</div>
			<a href="/issues" class="btn btn-secondary">Back to Issues</a>
		{:else if issue}
			<!-- Header -->
			<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 2rem; gap: 1rem;">
				<div style="flex: 1;">
					<h1 style="font-size: 2rem; font-weight: bold; color: #111827; margin-bottom: 0.5rem;">{issue.title}</h1>
					<div style="display: flex; align-items: center; gap: 1rem;">
						<span class="badge badge-{issue.status.toLowerCase()}">{issue.status}</span>
						<span class="badge badge-{issue.severity.toLowerCase()}">{issue.severity}</span>
					</div>
				</div>
				<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
					<a href="/issues" class="btn btn-secondary">Back to Issues</a>
					
					{#if canEdit}
						<a href="/issues/{issue.id}/edit" class="btn btn-secondary">Edit</a>
					{/if}
					
					{#if canAdvanceStatus && statusWorkflow[issue.status]}
						<button 
							on:click={advanceStatus}
							disabled={advancing}
							class="btn btn-blue"
						>
							{advancing ? 'Advancing...' : `Move to ${statusWorkflow[issue.status]}`}
						</button>
					{/if}
					
					{#if canDelete}
						<button 
							on:click={deleteIssue}
							class="btn btn-danger"
						>
							Delete
						</button>
					{/if}
				</div>
			</div>

			<!-- Issue Details -->
			<div style="background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
				<!-- Metadata -->
				<div style="padding: 1.5rem; border-bottom: 1px solid #e5e7eb;">
					<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
						<div>
							<dt style="font-size: 0.875rem; font-weight: 500; color: #6b7280;">Created</dt>
							<dd style="margin-top: 0.25rem; font-size: 0.875rem; color: #111827;">{formatDate(issue.created_at)}</dd>
						</div>
						<div>
							<dt style="font-size: 0.875rem; font-weight: 500; color: #6b7280;">Last Updated</dt>
							<dd style="margin-top: 0.25rem; font-size: 0.875rem; color: #111827;">{formatDate(issue.updated_at)}</dd>
						</div>
						<div>
							<dt style="font-size: 0.875rem; font-weight: 500; color: #6b7280;">Status</dt>
							<dd style="margin-top: 0.25rem;">
								<span class="badge badge-{issue.status.toLowerCase()}">{issue.status}</span>
							</dd>
						</div>
						<div>
							<dt style="font-size: 0.875rem; font-weight: 500; color: #6b7280;">Severity</dt>
							<dd style="margin-top: 0.25rem;">
								<span class="badge badge-{issue.severity.toLowerCase()}">{issue.severity}</span>
							</dd>
						</div>
					</div>
				</div>

				<!-- Attachment -->
				{#if issue.file_name}
					<div style="padding: 1.5rem; border-bottom: 1px solid #e5e7eb;">
						<h3 style="font-size: 1.125rem; font-weight: 500; color: #111827; margin-bottom: 0.75rem;">Attachment</h3>
						<div style="display: flex; align-items: center; gap: 0.75rem;">
							<div style="flex-shrink: 0;">
								<svg style="height: 2rem; width: 2rem; color: #6b7280;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
								</svg>
							</div>
							<div style="flex: 1; min-width: 0;">
								<p style="font-size: 0.875rem; font-weight: 500; color: #111827; margin: 0; overflow: hidden; text-overflow: ellipsis;">{issue.file_name}</p>
							</div>
							<div style="flex-shrink: 0;">
								<button 
									on:click={downloadFile}
									class="btn btn-secondary btn-sm"
								>
									Download
								</button>
							</div>
						</div>
					</div>
				{/if}

				<!-- Description -->
				<div style="padding: 1.5rem;">
					<h3 style="font-size: 1.125rem; font-weight: 500; color: #111827; margin-bottom: 1rem;">Description</h3>
					<div style="color: #374151;">
						{@html markdownToHtml(issue.description)}
					</div>
				</div>
			</div>

			<!-- Status Workflow -->
			<div style="margin-top: 2rem; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 1.5rem;">
				<h3 style="font-size: 1.125rem; font-weight: 500; color: #111827; margin-bottom: 1rem;">Status Workflow</h3>
				<div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
					{#each ['OPEN', 'TRIAGED', 'IN_PROGRESS', 'DONE'] as status, index}
						<div style="display: flex; align-items: center;">
							<div style="display: flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; border-radius: 50%; font-size: 0.875rem; font-weight: 500; {issue.status === status ? 'background-color: #2563eb; color: white;' : 'background-color: #e5e7eb; color: #6b7280;'}">
								{index + 1}
							</div>
							<span style="margin-left: 0.5rem; font-size: 0.875rem; font-weight: 500; {issue.status === status ? 'color: #111827;' : 'color: #6b7280;'}">
								{status.replace('_', ' ')}
							</span>
							{#if index < 3}
								<svg style="margin-left: 1rem; width: 1.25rem; height: 1.25rem; color: #d1d5db;" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
								</svg>
							{/if}
						</div>
					{/each}
				</div>
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

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
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
	.btn-blue:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-danger {
		background-color: #dc2626;
		color: white;
	}
	.btn-danger:hover {
		background-color: #b91c1c;
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
</style>
