

@app.route('/code')
@login_required
def code_dashboard():
    # Get all user's projects with their generations
    user_projects = user_db.get_user_projects(current_user.id)

    recent_generations = []
    for project in user_projects:
        project_generations = user_db.get_project_generations(project['id'], current_user.id)
        for gen in project_generations:
            gen['project_name'] = project['name']
            recent_generations.append(gen)

    # Sort by creation date, most recent first
    recent_generations.sort(key=lambda x: x['created_at'], reverse=True)
    recent_generations = recent_generations[:10]  # Show last 10

    return render_template('code.html',
                           projects=user_projects,
                           recent_generations=recent_generations)


@app.route('/projects/<project_id>/generate', methods=['GET', 'POST'])
@login_required
def new_generation(project_id):
    project = user_db.get_project(project_id, current_user.id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))

    form = CodeGenerationForm()

    if form.validate_on_submit():
        technology_stack = {
            'primary_language': form.primary_language.data,
            'frontend_framework': form.frontend_framework.data,
            'backend_framework': form.backend_framework.data,
            'database_type': form.database_type.data
        }

        generation_config = {
            'include_authentication': form.include_authentication.data,
            'include_api_docs': form.include_api_docs.data,
            'include_tests': form.include_tests.data,
            'include_docker': form.include_docker.data,
            'include_deployment': form.include_deployment.data,
            'additional_features': form.additional_features.data
        }

        generation_id = user_db.create_generation(
            project_id=project_id,
            generation_name=form.generation_name.data,
            architecture_pattern=form.architecture_pattern.data,
            generation_type=form.generation_type.data,
            technology_stack=technology_stack,
            generation_config=generation_config
        )

        if generation_id:
            # Mock file generation - in real implementation this would be AI-generated
            mock_files = [
                ('src/app.py', 'main.py', 'python', 'Mock Flask application'),
                ('src/models.py', 'models.py', 'python', 'Mock database models'),
                ('tests/test_app.py', 'test_app.py', 'python', 'Mock unit tests'),
                ('README.md', 'README.md', 'markdown', 'Mock project documentation'),
                ('requirements.txt', 'requirements.txt', 'text', 'Mock dependencies')
            ]

            for file_path, file_name, file_type, content in mock_files:
                user_db.add_generated_file(generation_id, file_path, file_name, file_type, content)

            # Update generation as completed
            user_db.update_generation(generation_id, current_user.id,
                                      status='completed', progress=100)

            flash(f'Code generation "{form.generation_name.data}" completed successfully!', 'success')
            return redirect(url_for('view_generation', generation_id=generation_id))
        else:
            flash('Error creating generation. Please try again.', 'error')

    return render_template('code/generate.html', form=form, project=project)


@app.route('/generations/<generation_id>')
@login_required
def view_generation(generation_id):
    generation = user_db.get_generation(generation_id, current_user.id)
    if not generation:
        flash('Generation not found.', 'error')
        return redirect(url_for('code_dashboard'))

    # Get project details
    project = user_db.get_project(generation['project_id'], current_user.id)
    if not project:
        flash('Associated project not found.', 'error')
        return redirect(url_for('code_dashboard'))

    files = generation.get('files', [])

    return render_template('code/viewer.html',
                           generation=generation,
                           project=project,
                           files=files)


@app.route('/generations/<generation_id>/download')
@login_required
def download_generation(generation_id):
    generation = user_db.get_generation(generation_id, current_user.id)
    if not generation:
        flash('Generation not found.', 'error')
        return redirect(url_for('code_dashboard'))

    # In a real implementation, this would create a ZIP file
    # For now, return a simple response
    flash('Download feature would create a ZIP file with all generated files.', 'info')
    return redirect(url_for('view_generation', generation_id=generation_id))


@app.route('/generations/<generation_id>/config', methods=['GET', 'POST'])
@login_required
def generation_config(generation_id):
    generation = user_db.get_generation(generation_id, current_user.id)
    if not generation:
        flash('Generation not found.', 'error')
        return redirect(url_for('code_dashboard'))

    form = GenerationConfigForm()

    if form.validate_on_submit():
        success = user_db.update_generation(
            generation_id=generation_id,
            user_id=current_user.id,
            generation_name=form.generation_name.data,
            status=form.status.data,
            progress=int(form.progress.data)
        )

        if success:
            flash('Generation updated successfully.', 'success')
            return redirect(url_for('view_generation', generation_id=generation_id))
        else:
            flash('Error updating generation. Please try again.', 'error')
    else:
        # Pre-populate form with current generation data
        form.generation_name.data = generation['generation_name']
        form.status.data = generation['status']
        form.progress.data = str(generation['progress'])

    return render_template('code/config.html', form=form, generation=generation)


@app.route('/generations/<generation_id>/delete', methods=['POST'])
@login_required
def delete_generation(generation_id):
    generation = user_db.get_generation(generation_id, current_user.id)
    if not generation:
        flash('Generation not found.', 'error')
        return redirect(url_for('code_dashboard'))

    if user_db.delete_generation(generation_id, current_user.id):
        flash(f'Generation "{generation["generation_name"]}" deleted successfully.', 'success')
    else:
        flash('Error deleting generation. Please try again.', 'error')

    return redirect(url_for('code_dashboard'))


@app.route('/projects/<project_id>/code')
@login_required
def project_code(project_id):
    project = user_db.get_project(project_id, current_user.id)
    if not project:
        flash('Project not found.', 'error')
        return redirect(url_for('projects'))

    generations = user_db.get_project_generations(project_id, current_user.id)

    return render_template('code/project_code.html',
                           project=project,
                           generations=generations)


@app.route('/api/files/<file_id>')
@login_required
def get_file_content(file_id):
    # This would get file content by ID for the code viewer
    # For now, return mock content
    return jsonify({
        'content': '# Mock file content\n# This would contain actual generated code',
        'file_type': 'python'
    })


@app.route('/api/generations/<generation_id>/progress')
@login_required
def generation_progress(generation_id):
    generation = user_db.get_generation(generation_id, current_user.id)
    if not generation:
        return jsonify({'error': 'Generation not found'}), 404

    return jsonify({
        'progress': generation['progress'],
        'status': generation['status'],
        'file_count': len(generation.get('files', []))
    })