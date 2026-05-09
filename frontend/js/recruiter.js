async function loadRecruiterDashboard() {
  try {
    const res  = await fetch(API + '/jobs/my/postings', { headers: authHeaders() });
    const jobs = await res.json();

    const totalJobs         = jobs.length;
    const totalApplications = jobs.reduce(function(sum, j) {
      return sum + (j.total_applications || 0);
    }, 0);
    const totalShortlisted  = jobs.reduce(function(sum, j) {
      return sum + (j.shortlisted_count || 0);
    }, 0);
    const totalAccepted     = jobs.reduce(function(sum, j) {
      return sum + (j.accepted_count || 0);
    }, 0);

    document.getElementById('stat-jobs').textContent        = totalJobs;
    document.getElementById('stat-total').textContent       = totalApplications;
    document.getElementById('stat-shortlisted').textContent = totalShortlisted;
    document.getElementById('stat-accepted').textContent    = totalAccepted;

    const el = document.getElementById('jobs-overview');
    if (jobs.length === 0) {
      el.innerHTML =
        '<div class="empty-state">' +
        '<p>No job postings yet.</p>' +
        '<a href="/recruiter/post_job.html" class="btn btn-primary btn-sm">' +
        'Post Your First Job</a></div>';
      return;
    }

    el.innerHTML = jobs.map(function(j) {
      return '<div style="display:flex; align-items:center; justify-content:space-between;' +
             'padding:14px 0; border-bottom:1px solid #f1f5f9;">' +
             '<div>' +
             '<div style="font-size:14px; font-weight:600; color:#1e293b;">' +
             j.job_title + '</div>' +
             '<div style="font-size:12px; color:#64748b; margin-top:3px;">' +
             'Total: ' + (j.total_applications || 0) +
             ' &nbsp;·&nbsp; Shortlisted: ' + (j.shortlisted_count || 0) +
             ' &nbsp;·&nbsp; Accepted: ' + (j.accepted_count || 0) +
             '</div>' +
             '</div>' +
             '<a href="/recruiter/applicants.html?id=' + j.job_id + '"' +
             ' class="btn btn-primary btn-sm">View Applicants</a>' +
             '</div>';
    }).join('');

  } catch (err) {
    console.error('Dashboard error:', err);
  }
}


async function loadSkillsChecklist() {
  try {
    const res    = await fetch(API + '/students/all-skills');
    const skills = await res.json();
    const el     = document.getElementById('skills-checklist');

    if (!el) return;

    el.innerHTML = skills.map(function(s) {
      return '<div style="display:flex; align-items:center; justify-content:space-between;' +
             'padding:10px 0; border-bottom:1px solid #f1f5f9;">' +
             '<div style="display:flex; align-items:center; gap:10px;">' +
             '<input type="checkbox" id="skill-' + s.skill_id + '"' +
             ' value="' + s.skill_id + '"' +
             ' style="width:16px; height:16px; cursor:pointer;">' +
             '<label for="skill-' + s.skill_id + '"' +
             ' style="font-size:13px; font-weight:600; color:#1e293b; cursor:pointer;">' +
             s.skill_name +
             '</label>' +
             '<span style="font-size:11px; color:#64748b;">' + s.category + '</span>' +
             '</div>' +
             '<select id="weight-' + s.skill_id + '"' +
             ' style="padding:5px 10px; border:1px solid #e2e8f0; border-radius:6px;' +
             ' font-size:12px; color:#1e293b; background:white;">' +
             '<option value="1.0">Required (1.0)</option>' +
             '<option value="0.5">Preferred (0.5)</option>' +
             '</select>' +
             '</div>';
    }).join('');

  } catch (err) {
    console.error('Could not load skills:', err);
  }
}


async function submitJob() {
  const title       = document.getElementById('job-title').value.trim();
  const description = document.getElementById('job-description').value.trim();
  const minCgpa     = parseFloat(document.getElementById('job-cgpa').value);
  const salary      = parseFloat(document.getElementById('job-salary').value);
  const deadline    = document.getElementById('job-deadline').value;

  if (!title || !description || !minCgpa || !salary || !deadline) {
    showAlert('alert-post', 'Please fill in all job details.', 'error');
    return;
  }

  const skillCheckboxes = document.querySelectorAll('#skills-checklist input[type="checkbox"]:checked');
  if (skillCheckboxes.length === 0) {
    showAlert('alert-post', 'Please select at least one required skill.', 'error');
    return;
  }

  const skills = [];
  skillCheckboxes.forEach(function(cb) {
    const skillId = parseInt(cb.value);
    const weight  = parseFloat(document.getElementById('weight-' + skillId).value);
    skills.push({ skill_id: skillId, weight: weight });
  });

  try {
    const res  = await fetch(API + '/jobs/', {
      method:  'POST',
      headers: authHeaders(),
      body:    JSON.stringify({
        title:       title,
        description: description,
        min_cgpa:    minCgpa,
        deadline:    deadline,
        salary:      salary,
        skills:      skills
      })
    });
    const data = await res.json();

    if (!res.ok) {
      showAlert('alert-post', data.detail || 'Could not post job.', 'error');
      return;
    }

    showAlert('alert-post',
      'Job posted successfully! Redirecting to your job postings...',
      'success'
    );
    setTimeout(function() {
      window.location.href = '/recruiter/my_jobs.html';
    }, 1500);

  } catch (err) {
    showAlert('alert-post', 'Could not connect to server.', 'error');
  }
}


// ── NEW: Delete (or close) a job posting ─────────────────────────────────────
async function deleteJob(jobId) {
  const confirmed = confirm(
    'Are you sure you want to delete this job?\n\n' +
    '• If it has no applications it will be permanently deleted.\n' +
    '• If it already has applications it will be closed instead.'
  );
  if (!confirmed) return;

  try {
    const res  = await fetch(API + '/jobs/' + jobId, {
      method:  'DELETE',
      headers: authHeaders()
    });
    const data = await res.json();

    if (!res.ok) {
      showAlert('alert-jobs', data.detail || 'Could not delete job.', 'error');
      return;
    }

    showAlert('alert-jobs', data.message, 'success');
    // Refresh the list so the deleted/closed job disappears or updates
    setTimeout(function() { loadMyJobs(); }, 900);

  } catch (err) {
    showAlert('alert-jobs', 'Could not connect to server.', 'error');
  }
}
// ─────────────────────────────────────────────────────────────────────────────


async function loadMyJobs() {
  const el = document.getElementById('jobs-list');
  try {
    const res  = await fetch(API + '/jobs/my/postings', { headers: authHeaders() });
    const jobs = await res.json();

    if (jobs.length === 0) {
      el.innerHTML =
        '<div class="card"><div class="empty-state">' +
        '<p>You have not posted any jobs yet.</p>' +
        '<a href="/recruiter/post_job.html" class="btn btn-primary btn-sm">' +
        'Post Your First Job</a></div></div>';
      return;
    }

    el.innerHTML = jobs.map(function(j) {
      return '<div class="card" style="margin-bottom:16px;">' +
             '<div style="display:flex; justify-content:space-between;' +
             'align-items:flex-start; margin-bottom:16px;">' +
             '<div>' +
             '<h3 style="font-size:17px; font-weight:700; color:#1e293b; margin-bottom:4px;">' +
             j.job_title + '</h3>' +
             '<p style="font-size:13px; color:#64748b;">' + j.company_name + '</p>' +
             '</div>' +

             // ── Buttons row (View Applicants + Delete) ────────────────────
             '<div style="display:flex; gap:8px; align-items:center;">' +
             '<a href="/recruiter/applicants.html?id=' + j.job_id + '"' +
             ' class="btn btn-primary btn-sm">View Applicants</a>' +
             '<button onclick="deleteJob(' + j.job_id + ')"' +
             ' style="padding:6px 14px; border-radius:6px; font-size:12px;' +
             ' font-weight:600; cursor:pointer; border:1px solid #fca5a5;' +
             ' background:#fee2e2; color:#dc2626; transition:background 0.15s;"' +
             ' onmouseover="this.style.background=\'#fecaca\'"' +
             ' onmouseout="this.style.background=\'#fee2e2\'">Delete</button>' +
             '</div>' +
             // ─────────────────────────────────────────────────────────────

             '</div>' +
             '<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px;">' +
             '<div style="background:#f8fafc; border-radius:8px; padding:12px; text-align:center;">' +
             '<div style="font-size:11px; color:#64748b; margin-bottom:4px;">TOTAL</div>' +
             '<div style="font-size:20px; font-weight:700; color:#1e293b;">' +
             (j.total_applications || 0) + '</div></div>' +
             '<div style="background:#f8fafc; border-radius:8px; padding:12px; text-align:center;">' +
             '<div style="font-size:11px; color:#64748b; margin-bottom:4px;">SUBMITTED</div>' +
             '<div style="font-size:20px; font-weight:700; color:#64748b;">' +
             (j.submitted_count || 0) + '</div></div>' +
             '<div style="background:#dcfce7; border-radius:8px; padding:12px; text-align:center;">' +
             '<div style="font-size:11px; color:#16a34a; margin-bottom:4px;">SHORTLISTED</div>' +
             '<div style="font-size:20px; font-weight:700; color:#16a34a;">' +
             (j.shortlisted_count || 0) + '</div></div>' +
             '<div style="background:#ebf2ff; border-radius:8px; padding:12px; text-align:center;">' +
             '<div style="font-size:11px; color:#1a56db; margin-bottom:4px;">ACCEPTED</div>' +
             '<div style="font-size:20px; font-weight:700; color:#1a56db;">' +
             (j.accepted_count || 0) + '</div></div>' +
             '</div></div>';
    }).join('');

  } catch (err) {
    if (el) showAlert('alert-jobs', 'Could not load job postings.', 'error');
  }
}


async function loadApplicants() {
  const params = new URLSearchParams(window.location.search);
  const jobId  = params.get('id');

  if (!jobId) {
    window.location.href = '/recruiter/my_jobs.html';
    return;
  }

  window.currentJobId = jobId;

  try {
    const res  = await fetch(API + '/applications/ranked/' + jobId, {
      headers: authHeaders()
    });
    const applicants = await res.json();

    if (applicants.length > 0) {
      document.getElementById('job-title-heading').textContent =
        applicants[0].job_title || 'Applicants';
      document.getElementById('job-subtitle').textContent =
        applicants[0].company_name + ' · Ranked by AI match score';
    }

    const submitted   = applicants.filter(function(a) { return a.status === 'submitted'; }).length;
    const shortlisted = applicants.filter(function(a) { return a.status === 'shortlisted'; }).length;
    const accepted    = applicants.filter(function(a) { return a.status === 'accepted'; }).length;

    document.getElementById('count-total').textContent       = applicants.length;
    document.getElementById('count-submitted').textContent   = submitted;
    document.getElementById('count-shortlisted').textContent = shortlisted;
    document.getElementById('count-accepted').textContent    = accepted;

    const tbody = document.getElementById('applicants-body');

    if (applicants.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="8" style="text-align:center; padding:40px; color:#64748b;">' +
        'No applicants yet for this job.</td></tr>';
      return;
    }

    tbody.innerHTML = applicants.map(function(a, i) {
      const rankColors = ['#f59e0b', '#94a3b8', '#cd7c3a'];
      const rankColor  = rankColors[i] || '#1a56db';
      const score      = a.match_score != null ? parseFloat(a.match_score) : null;
      const date       = new Date(a.apply_date).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric'
      });

      return '<tr>' +
        '<td>' +
        '<div style="width:28px; height:28px; border-radius:50%;' +
        'background:' + rankColor + '; color:white; display:flex;' +
        'align-items:center; justify-content:center;' +
        'font-size:12px; font-weight:700;">' +
        (a.rank_position || i + 1) + '</div>' +
        '</td>' +
        '<td>' +
        '<div style="font-size:13px; font-weight:600; color:#1e293b;">' +
        a.student_name + '</div>' +
        '<div style="font-size:11px; color:#64748b;">' + a.student_email + '</div>' +
        '</td>' +
        '<td>' + a.cgpa + '</td>' +
        '<td>' + (a.major || '—') + '</td>' +
        '<td>' +
        (score !== null
          ? '<div class="score-bar-wrap">' +
            '<div class="score-bar">' +
            '<div class="score-fill" style="width:' + score + '%;"></div>' +
            '</div>' +
            '<span class="score-text">' + score.toFixed(1) + '</span>' +
            '</div>'
          : '—') +
        '</td>' +
        '<td><span class="badge badge-' + a.status + '">' + a.status + '</span></td>' +
        '<td>' + date + '</td>' +
        '<td>' +
        '<select onchange="updateStatus(' + a.application_id + ', this.value)"' +
        ' style="padding:6px 10px; border:1px solid #e2e8f0; border-radius:6px;' +
        ' font-size:12px; color:#1e293b; background:white; cursor:pointer;">' +
        '<option value="">-- Change --</option>' +
        '<option value="shortlisted">Shortlist</option>' +
        '<option value="accepted">Accept</option>' +
        '<option value="rejected">Reject</option>' +
        '</select>' +
        '</td>' +
        '</tr>';
    }).join('');

  } catch (err) {
    showAlert('alert-applicants', 'Could not load applicants.', 'error');
  }
}


async function updateStatus(applicationId, newStatus) {
  if (!newStatus) return;

  try {
    const res  = await fetch(API + '/applications/status', {
      method:  'PUT',
      headers: authHeaders(),
      body:    JSON.stringify({
        application_id: applicationId,
        new_status:     newStatus
      })
    });
    const data = await res.json();

    if (!res.ok) {
      showAlert('alert-applicants', data.detail || 'Could not update status.', 'error');
      return;
    }

    showAlert('alert-applicants', data.message, 'success');

    setTimeout(function() { loadApplicants(); }, 800);

  } catch (err) {
    showAlert('alert-applicants', 'Could not connect to server.', 'error');
  }
}


async function rerank() {
  const jobId = window.currentJobId;
  if (!jobId) return;

  const btn       = document.getElementById('rerank-btn');
  btn.textContent = 'Recalculating...';
  btn.disabled    = true;

  try {
    const res  = await fetch(API + '/applications/rerank/' + jobId, {
      method:  'POST',
      headers: authHeaders()
    });
    const data = await res.json();

    showAlert('alert-applicants', data.message, 'success');
    setTimeout(function() { loadApplicants(); }, 800);

  } catch (err) {
    showAlert('alert-applicants', 'Could not recalculate rankings.', 'error');
  } finally {
    btn.textContent = 'Recalculate Rankings';
    btn.disabled    = false;
  }
}