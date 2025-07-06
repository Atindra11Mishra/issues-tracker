<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let title = '';
	let description = '';
	let severity = 'MEDIUM';
	let file = null;
	let loading = false;
	let error = '';
	let preview = false;

	onMount(() => {
		const token = localStorage.getItem('token');
		if (!token) {
			goto('/login');
		}
	});

	async function createIssue() {
		if (!title.trim() || !description.trim()) {
			error = 'Please fill in all required fields';
			return;
		}

		loading = true;
		error = '';

		try {
			const token = localStorage.getItem('token');
			if (!token) {
				throw new Error('No authentication token found');
			}

			const formData = new FormData();
			formData.append('title', title.trim());
			formData.append('description', description.trim());
			formData.append('severity', severity);
			
			if (file) {
				formData.append('file', file);
			}

			console.log('Sending request to create issue...');
			const response = await fetch('http://localhost:8000/issues', {
				method: 'POST',
				headers: {
					'Authorization': `Bearer ${token}`
					// Don't set Content-Type for FormData, let browser set it
				},
				body: formData
			});

			console.log('Response status:', response.status);
			console.log('Response headers:', response.headers);

			if (!response.ok) {
				const errorText = await response.text();
				console.error('Error response:', errorText);
				try {
					const errorData = JSON.parse(errorText);
					throw new Error(errorData.detail || `Server error: ${response.status}`);
				} catch (parseError) {
					throw new Error(`Server error: ${response.status} - ${errorText}`);
				}
			}

			const result = await response.json();
			console.log('Issue created successfully:', result);
			
			// Redirect to the new issue
			goto(`/issues/${result.id}`);
		} catch (err) {
			console.error('Create issue error:', err);
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function handleFileChange(event) {
		file = event.target.files[0];
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
</script>

<div style="min-height: 100vh; background-color: #f9fafb; padding: 2rem;">
	<div style="max-width: 1000px; margin: 0 auto;">
		<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
			<h1 style="font-size: 2rem; font-weight: bold; color: #111827;">Create New Issue</h1>
			<a href="/issues" class="btn btn-secondary">Back to Issues</a>
		</div>

		{#if error}
			<div class="alert alert-error">
				{error}
			</div>
		{/if}

		<div style="background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
			<form on:submit|preventDefault={createIssue} style="padding: 1.5rem;">
				<div class="form-group">
					<label for="title" class="form-label">Title *</label>
					<input
						type="text"
						id="title"
						bind:value={title}
						placeholder="Brief description of the issue"
						required
						class="form-input"
						disabled={loading}
					/>
				</div>

				<div class="form-group">
					<label for="severity" class="form-label">Severity</label>
					<select
						id="severity"
						bind:value={severity}
						class="form-input"
						disabled={loading}
					>
						<option value="LOW">Low</option>
						<option value="MEDIUM">Medium</option>
						<option value="HIGH">High</option>
						<option value="CRITICAL">Critical</option>
					</select>
				</div>

				<div class="form-group">
					<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
						<label class="form-label">Description * (Markdown supported)</label>
						<button
							type="button"
							on:click={togglePreview}
							style="color: #2563eb; text-decoration: none; font-size: 0.875rem; background: none; border: none; cursor: pointer;"
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
							placeholder="Detailed description of the issue. You can use Markdown formatting:

# Heading
## Subheading
**Bold text**
*Italic text*
`code`

- List item 1
- List item 2"
							required
							rows="10"
							class="form-input"
							disabled={loading}
						></textarea>
					{/if}
				</div>

				<div class="form-group">
					<label for="file" class="form-label">Attachment (optional)</label>
					<input
						type="file"
						id="file"
						on:change={handleFileChange}
						class="form-input"
						disabled={loading}
					/>
					{#if file}
						<p style="margin-top: 0.5rem; font-size: 0.875rem; color: #6b7280;">
							Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
						</p>
					{/if}
				</div>

				<div style="display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem;">
					<a href="/issues" class="btn btn-secondary">Cancel</a>
					<button
						type="submit"
						class="btn btn-primary"
						disabled={loading}
					>
						{loading ? 'Creating...' : 'Create Issue'}
					</button>
				</div>
			</form>
		</div>

		<!-- Markdown Help -->
		<div style="margin-top: 2rem; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 1.5rem;">
			<h3 style="font-size: 1.125rem; font-weight: 500; color: #111827; margin-bottom: 1rem;">Markdown Quick Reference</h3>
			<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.875rem;">
				<div>
					<h4 style="font-weight: 500; color: #374151; margin-bottom: 0.5rem;">Formatting</h4>
					<ul style="color: #6b7280; margin: 0; padding-left: 1rem;">
						<li><code>**bold text**</code> → <strong>bold text</strong></li>
						<li><code>*italic text*</code> → <em>italic text</em></li>
						<li><code>`code`</code> → <code style="background-color: #f3f4f6; padding: 0.125rem; border-radius: 0.25rem;">code</code></li>
					</ul>
				</div>
				<div>
					<h4 style="font-weight: 500; color: #374151; margin-bottom: 0.5rem;">Headers</h4>
					<ul style="color: #6b7280; margin: 0; padding-left: 1rem;">
						<li><code># Heading 1</code></li>
						<li><code>## Heading 2</code></li>
						<li><code>### Heading 3</code></li>
					</ul>
				</div>
			</div>
		</div>
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
	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-secondary {
		background-color: white;
		color: #374151;
		border: 1px solid #d1d5db;
	}
	.btn-secondary:hover {
		background-color: #f9fafb;
	}

	.form-group {
		margin-bottom: 1.5rem;
	}

	.form-label {
		display: block;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		margin-bottom: 0.5rem;
	}

	.form-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		box-sizing: border-box;
	}

	.form-input:focus {
		outline: none;
		border-color: #2563eb;
		box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
	}

	.form-input:disabled {
		opacity: 0.6;
		cursor: not-allowed;
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

	textarea.form-input {
		resize: vertical;
		min-height: 200px;
	}
</style>