<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api } from '$lib/api';

	let issue = null;
	let currentUser = null;
	let title = '';
	let description = '';
	let severity = 'MEDIUM';
	let status = 'OPEN';
	let loading = true;
	let saving = false;
	let error = '';
	let preview = false;

	onMount(async () => {
		const issueId = $page.params.id;
		await loadCurrentUser();
		await loadIssue(issueId);
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
			if (err.message.includes('401') || err.message.includes('unauthorized')) {
				localStorage.removeItem('token');
				goto('/login');
			}
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
			
			// Populate form
			title = issue.title;
			description = issue.description;
			severity = issue.severity;
			status = issue.status;

			// Check if user has permission to edit this issue
			if (currentUser && currentUser.role === 'REPORTER' && issue.creator_id !== currentUser.id) {
				error = 'You do not have permission to edit this issue.';
				return;
			}
		} catch (err) {
			error = err.message;
			if (err.message.includes('404')) {
				error = 'Issue not found or you do not have permission to edit it.';
			} else if (err.message.includes('401')) {
				localStorage.removeItem('token');
				goto('/login');
			}
		} finally {
			loading = false;
		}
	}

	async function updateIssue() {
		if (!title.trim() || !description.trim()) {
			error = 'Please fill in all required fields';
			return;
		}

		saving = true;
		error = '';

		try {
			const token = localStorage.getItem('token');
			const updateData = {
				title: title.trim(),
				description: description.trim(),
				severity,
			};

			// Only include status if user is not a reporter
			if (currentUser && currentUser.role !== 'REPORTER') {
				updateData.status = status;
			}

			await api(`/issues/${issue.id}`, {
				method: 'PUT',
				headers: { 
					Authorization: `Bearer ${token}`,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(updateData)
			});

			goto(`/issues/${issue.id}`);
		} catch (err) {
			error = err.message;
		} finally {
			saving = false;
		}
	}

	function togglePreview() {
		preview = !preview;
	}

	function markdownToHtml(markdown) {
		return markdown
			.replace(/### (.*$)/gim, '<h3 style="font-size: 1.125rem; font-weight: 600; margin: 1rem 0 0.5rem 0;">$1</h3>')
			.replace(/## (.*$)/gim, '<h2 style="font-size: 1.25rem; font-weight: 600; margin: 1rem 0 0.5rem 0;">$1</h2>')
			.replace(/# (.*$)/gim, '<h1 style="font-size: 1.5rem; font-weight: 700; margin: 1rem 0 0.5rem 0;">$1</h1>')
			.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
			.replace(/\*(.*?)\*/gim, '<em>$1</em>')
			.replace(/`(.*?)`/gim, '<code style="background-color: #f3f4f6; padding: 0.125rem 0.25rem; border-radius: 0.25rem;">$1</code>')
			.replace(/\n/gim, '<br>');
	}

	// Check if user can edit status (only maintainers and admins)
	$: canEditStatus = currentUser && ['MAINTAINER', 'ADMIN'].includes(currentUser.role);
</script>

<div style="min-height: 100vh; background-color: #f9fafb; padding: 2rem;">
	<div style="max-width: 1000px; margin: 0 auto;">
		{#if loading}
			<div style="text-align: center; padding: 2rem;">
				<div style="width: 3rem; height: 3rem; border: 0.125rem solid #e5e7eb; border-top: 0.125rem solid #2563eb; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto;"></div>
				<p style="margin-top: 1rem; color: #6b7280;">Loading issue...</p>
			</div>
		{:else}
			<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
				<h1 style="font-size: 2rem; font-weight: bold; color: #111827;">Edit Issue</h1>
				<a href="/issues/{issue?.id}" style="display: inline-flex; align-items: center; padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 500; border-radius: 0.375rem; text-decoration: none; background-color: white; color: #374151; border: 1px solid #d1d5db;">Back to Issue</a>
			</div>

			{#if error}
				<div style="background-color: #fee2e2; border: 1px solid #fca5a5; color: #dc2626; padding: 1rem; border-radius: 0.375rem; margin-bottom: 1.5rem;">
					{error}
				</div>
			{/if}

			{#if issue && currentUser}
				<div style="background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
					<form on:submit|preventDefault={updateIssue} style="padding: 1.5rem;">
						<!-- Title -->
						<div style="margin-bottom: 1.5rem;">
							<label for="title" style="display: block; font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 0.5rem;">
								Title *
							</label>
							<input
								type="text"
								id="title"
								bind:value={title}
								placeholder="Brief description of the issue"
								required
								style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem; box-sizing: border-box;"
								disabled={saving}
							/>
						</div>

						<!-- Status and Severity -->
						<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
							{#if canEditStatus}
								<div>
									<label for="status" style="display: block; font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 0.5rem;">
										Status
									</label>
									<select
										id="status"
										bind:value={status}
										style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem; box-sizing: border-box;"
										disabled={saving}
									>
										<option value="OPEN">Open</option>
										<option value="TRIAGED">Triaged</option>
										<option value="IN_PROGRESS">In Progress</option>
										<option value="DONE">Done</option>
									</select>
								</div>
							{:else}
								<div>
									<label style="display: block; font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 0.5rem;">
										Current Status
									</label>
									<div style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background-color: #f9fafb;">
										<span style="display: inline-flex; align-items: center; padding: 0.25rem 0.625rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; background-color: #fee2e2; color: #dc2626;">{status}</span>
									</div>
									<p style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">Status can only be changed by Maintainers and Admins</p>
								</div>
							{/if}

							<div>
								<label for="severity" style="display: block; font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 0.5rem;">
									Severity
								</label>
								<select
									id="severity"
									bind:value={severity}
									style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem; box-sizing: border-box;"
									disabled={saving}
								>
									<option value="LOW">Low</option>
									<option value="MEDIUM">Medium</option>
									<option value="HIGH">High</option>
									<option value="CRITICAL">Critical</option>
								</select>
							</div>
						</div>

						<!-- Description -->
						<div style="margin-bottom: 1.5rem;">
							<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
								<label style="display: block; font-size: 0.875rem; font-weight: 500; color: #374151;">
									Description * (Markdown supported)
								</label>
								<button
									type="button"
									on:click={togglePreview}
									style="font-size: 0.875rem; color: #2563eb; background: none; border: none; cursor: pointer;"
								>
									{preview ? 'Edit' : 'Preview'}
								</button>
							</div>
							
							{#if preview}
								<div style="width: 100%; min-height: 200px; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; background-color: #f9fafb;">
									{@html markdownToHtml(description)}
								</div>
							{:else}
								<textarea
									id="description"
									bind:value={description}
									placeholder="Detailed description of the issue. You can use Markdown formatting."
									required
									rows="10"
									style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem; box-sizing: border-box; resize: vertical; min-height: 200px;"
									disabled={saving}
								></textarea>
							{/if}
						</div>

						<!-- Current File Info -->
						{#if issue.file_name}
							<div style="background-color: #f9fafb; border-radius: 0.375rem; padding: 1rem; margin-bottom: 1.5rem;">
								<h4 style="font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 0.5rem;">Current Attachment</h4>
								<div style="display: flex; align-items: center; gap: 0.5rem;">
									<svg style="height: 1.25rem; width: 1.25rem; color: #6b7280;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
									</svg>
									<span style="font-size: 0.875rem; color: #6b7280;">{issue.file_name}</span>
								</div>
								<p style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">Note: File attachments cannot be changed when editing. Create a new issue to upload a different file.</p>
							</div>
						{/if}

						<!-- Submit Button -->
						<div style="display: flex; justify-content: flex-end; gap: 1rem;">
							<a href="/issues/{issue.id}" style="display: inline-flex; align-items: center; padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 500; border-radius: 0.375rem; text-decoration: none; background-color: white; color: #374151; border: 1px solid #d1d5db;">
								Cancel
							</a>
							<button
								type="submit"
								style="display: inline-flex; align-items: center; padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 500; border-radius: 0.375rem; background-color: #2563eb; color: white; border: none; cursor: pointer;"
								disabled={saving}
							>
								{saving ? 'Saving...' : 'Save Changes'}
							</button>
						</div>
					</form>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
</style>