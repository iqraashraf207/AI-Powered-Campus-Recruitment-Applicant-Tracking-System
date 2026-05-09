async function loadDashboard() {
  try {
      const appsRes = await fetch(API + '/applications/my', { headers: authHeaders() });
      const apps = await appsRes.json();
      const profRes = await fetch(API + '/students/profile', { headers: authHeaders() });
      const profData = await profRes.json();
      const recRes = await fetch(API + '/recommendations/', { headers: authHeaders() });
      const recData = await recRes.json();
      const total = apps.length;
      const shortlisted = apps.filter(function (a) { return a.status === 'shortlisted'; }).length;
      const accepted = apps.filter(function (a) { return a.status === 'accepted'; }).length;
      document.getElementById('stat-total').textContent = total;
      document.getElementById('stat-shortlisted').textContent = shortlisted;
      document.getElementById('stat-accepted').textContent = accepted;
      document.getElementById('stat-cgpa').textContent =
          profData.profile ? profData.profile.cgpa : '—';
      const recentEl = document.getElementById('recent-applications');
      if (apps.length === 0) {
          recentEl.innerHTML =
              '<div class="empty-state"><p>No applications yet.</p>' +
              '<a href="/student/jobs.html" class="btn btn-primary btn-sm">Browse Jobs</a></div>';
      } else {
          recentEl.innerHTML = apps.slice(0, 4).map(function (a) {
              return '<div style="display:flex; align-items:center; justify-content:space-between;' +
                  'padding:10px 0; border-bottom:1px solid #f1f5f9;">' +
                  '<div>' +
                  '<div style="font-size:13px; font-weight:600; color:#1e293b;">' + a.job_title + '</div>' +
                  '<div style="font-size:12px; color:#64748b;">' + a.company_name +
                  (a.match_score ? ' · Score: ' + a.match_score : '') + '</div>' +
                  '</div>' +
                  '<span class="badge badge-' + a.status + '">' + a.status + '</span>' +
                  '</div>';
          }).join('');
      }
      const recEl = document.getElementById('recommendations');
      const recs = recData.recommendations || [];
      if (recs.length === 0) {
          recEl.innerHTML =
              '<div class="empty-state"><p>No recommendations yet.</p>' +
              '<a href="/student/profile.html" class="btn btn-primary btn-sm">Complete Profile</a></div>';
      } else {
          recEl.innerHTML = recs.slice(0, 3).map(function (r) {
              const fit = parseFloat(r.rec_fit_score);
              return '<div style="display:flex; align-items:center; justify-content:space-between;' +
                  'padding:10px 0; border-bottom:1px solid #f1f5f9;">' +
                  '<div style="flex:1;">' +
                  '<div style="font-size:13px; font-weight:600; color:#1e293b;">' + r.rec_title + '</div>' +
                  '<div style="font-size:12px; color:#64748b;">' + r.rec_company + '</div>' +
                  '<div class="score-bar-wrap" style="margin-top:5px;">' +
                  '<div class="score-bar"><div class="score-fill" style="width:' + fit + '%;"></div></div>' +
                  '</div></div>' +
                  '<span style="font-size:13px; font-weight:700; color:#16a34a; margin-left:12px;">' +
                  fit.toFixed(1) + '%</span>' +
                  '</div>';
          }).join('');
      }
  } catch (err) {
      console.error('Dashboard error:', err);
  }
}

async function loadProfile() {
  try {
      const res = await fetch(API + '/students/profile', { headers: authHeaders() });
      const data = await res.json();
      if (data.profile) {
          document.getElementById('profile-name').value = data.profile.name || '';
          document.getElementById('profile-email').value = data.profile.email || '';
          document.getElementById('profile-cgpa').value = data.profile.cgpa || '';
          document.getElementById('profile-major').value = data.profile.major || '';
          document.getElementById('profile-grad-year').value = data.profile.graduation_year || '';
      }
      if (data.resume && data.resume.raw_text) {
          document.getElementById('resume-text').value = data.resume.raw_text;
      }
      renderSkills(data.skills || []);
  } catch (err) {
      showAlert('alert-profile', 'Could not load profile. Please refresh.', 'error');
  }
}


function renderSkills(skills) {
  const el = document.getElementById('skills-list');
  if (skills.length === 0) {
      el.innerHTML =
          '<div class="empty-state">' +
          '<p>No skills found yet. Submit your resume to extract skills automatically.</p>' +
          '</div>';
      return;
  }
  el.innerHTML = skills.map(function (s) {
      return '<div style="display:flex; align-items:center; justify-content:space-between;' +
          'padding:10px 0; border-bottom:1px solid #f1f5f9;">' +
          '<div>' +
          '<span style="font-size:13px; font-weight:600; color:#1e293b;">' + s.skill_name + '</span>' +
          '<span style="font-size:11px; color:#64748b; margin-left:8px;">' + s.category + '</span>' +
          '</div>' +
          '<select onchange="updateSkillProficiency(' + s.skill_id + ', this.value)"' +
          ' style="padding:5px 10px; border:1px solid #e2e8f0; border-radius:6px;' +
          ' font-size:12px; color:#1e293b; background:white; cursor:pointer;">' +
          '<option value="beginner"' + (s.proficiency_level === 'beginner' ? ' selected' : '') + '>Beginner</option>' +
          '<option value="intermediate"' + (s.proficiency_level === 'intermediate' ? ' selected' : '') + '>Intermediate</option>' +
          '<option value="advanced"' + (s.proficiency_level === 'advanced' ? ' selected' : '') + '>Advanced</option>' +
          '</select>' +
          '</div>';
  }).join('');
}


async function saveProfile() {
  const cgpa = parseFloat(document.getElementById('profile-cgpa').value);
  const major = document.getElementById('profile-major').value.trim();
  const gradYear = parseInt(document.getElementById('profile-grad-year').value);
  if (!cgpa || !major || !gradYear) {
      showAlert('alert-profile', 'Please fill in all profile fields.', 'error');
      return;
  }
  try {
      const res = await fetch(API + '/students/profile', {
          method: 'PUT',
          headers: authHeaders(),
          body: JSON.stringify({ cgpa: cgpa, major: major, graduation_year: gradYear })
      });
      const data = await res.json();
      if (!res.ok) {
          showAlert('alert-profile', data.detail || 'Could not save profile.', 'error');
          return;
      }
      showAlert('alert-profile', 'Profile saved successfully.', 'success');
  } catch (err) {
      showAlert('alert-profile', 'Could not connect to server.', 'error');
  }
}


async function submitResume() {
  const rawText = document.getElementById('resume-text').value.trim();
  if (!rawText) {
      showAlert('alert-resume', 'Please paste your resume text first.', 'error');
      return;
  }
  try {
      const res = await fetch(API + '/students/resume', {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ raw_text: rawText })
      });
      const data = await res.json();
      if (!res.ok) {
          showAlert('alert-resume', data.detail || 'Could not save resume.', 'error');
          return;
      }
      showAlert('alert-resume',
          'Resume saved. ' + data.skills_count + ' skills extracted. ' +
          data.experience_years + ' year(s) of experience detected.',
          'success'
      );
      loadProfile();
  } catch (err) {
      showAlert('alert-resume', 'Could not connect to server.', 'error');
  }
}


async function updateSkillProficiency(skillId, level) {
  try {
      await fetch(API + '/students/skills', {
          method: 'PUT',
          headers: authHeaders(),
          body: JSON.stringify({ skill_id: skillId, proficiency_level: level })
      });
  } catch (err) {
      console.error('Could not update skill:', err);
  }
}


let allJobs = [];

async function loadJobs() {
  try {
      const res = await fetch(API + '/jobs/', { headers: authHeaders() });
      const data = await res.json();
      allJobs = data;
      renderJobs(allJobs);
  } catch (err) {
      showAlert('alert-jobs', 'Could not load jobs.', 'error');
  }
}


function renderJobs(jobs) {
  const tbody = document.getElementById('jobs-table-body');
  if (!tbody) return;
  if (jobs.length === 0) {
      tbody.innerHTML =
          '<tr><td colspan="8" style="text-align:center; padding:32px; color:#64748b;">' +
          'No active jobs found.</td></tr>';
      return;
  }
  tbody.innerHTML = jobs.map(function (j) {
      const deadline = new Date(j.deadline).toLocaleDateString('en-GB', {
          day: 'numeric', month: 'short', year: 'numeric'
      });
      return '<tr>' +
          '<td><strong>' + j.title + '</strong></td>' +
          '<td>' + j.company_name + '</td>' +
          '<td>' + (j.location || '—') + '</td>' +
          '<td>Rs ' + Number(j.salary).toLocaleString() + '</td>' +
          '<td>' + j.min_cgpa + '</td>' +
          '<td>' + deadline + '</td>' +
          '<td>' + j.required_skill_count + ' skills</td>' +
          '<td><a href="/student/job_detail.html?id=' + j.job_id + '"' +
          ' class="btn btn-primary btn-sm">View & Apply</a></td>' +
          '</tr>';
  }).join('');
}


function filterJobs() {
  const query = document.getElementById('search-input').value.toLowerCase();
  const filtered = allJobs.filter(function (j) {
      return j.title.toLowerCase().includes(query) ||
          j.company_name.toLowerCase().includes(query);
  });
  renderJobs(filtered);
}

async function loadJobDetail() {
  const params = new URLSearchParams(window.location.search);
  const jobId = params.get('id');
  if (!jobId) { window.location.href = '/student/jobs.html'; return; }
  try {
      const res = await fetch(API + '/jobs/' + jobId, { headers: authHeaders() });
      const data = await res.json();
      if (!res.ok) { showAlert('alert-detail', 'Job not found.', 'error'); return; }
      const job = data.job;
      const skills = data.skills || [];
      const deadline = new Date(job.deadline).toLocaleDateString('en-GB', {
          day: 'numeric', month: 'short', year: 'numeric'
      });
      const required = skills.filter(function (s) { return s.weight === 1.0; });
      const preferred = skills.filter(function (s) { return s.weight < 1.0; });
      document.getElementById('job-detail-card').innerHTML =
          '<div style="display:flex; justify-content:space-between; align-items:flex-start;' +
          'margin-bottom:20px; padding-bottom:20px; border-bottom:1px solid #e2e8f0;">' +
          '<div>' +
          '<h2 style="font-size:22px; font-weight:700; color:#1e293b; margin-bottom:4px;">' +
          job.title + '</h2>' +
          '<p style="font-size:14px; color:#64748b;">' + job.company_name + ' · ' +
          (job.location || 'Pakistan') + '</p>' +
          '</div>' +
          '<button class="btn btn-primary" onclick="applyForJob(' + jobId + ')">Apply Now</button>' +
          '</div>' +
          '<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:24px;">' +
          '<div style="background:#f8fafc; border-radius:8px; padding:14px;">' +
          '<div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Salary</div>' +
          '<div style="font-size:16px; font-weight:700; color:#1e293b;">Rs ' + Number(job.salary).toLocaleString() + '</div></div>' +
          '<div style="background:#f8fafc; border-radius:8px; padding:14px;">' +
          '<div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Min CGPA</div>' +
          '<div style="font-size:16px; font-weight:700; color:#1e293b;">' + job.min_cgpa + '</div></div>' +
          '<div style="background:#f8fafc; border-radius:8px; padding:14px;">' +
          '<div style="font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">Deadline</div>' +
          '<div style="font-size:16px; font-weight:700; color:#1e293b;">' + deadline + '</div></div>' +
          '</div>' +
          '<div style="margin-bottom:20px;">' +
          '<h3 style="font-size:15px; font-weight:600; color:#1e293b; margin-bottom:10px;">Job Description</h3>' +
          '<p style="font-size:14px; color:#475569; line-height:1.7;">' + job.description + '</p></div>' +
          (required.length > 0 ?
              '<div style="margin-bottom:16px;"><h3 style="font-size:15px; font-weight:600; color:#1e293b; margin-bottom:10px;">Required Skills</h3>' +
              required.map(function (s) { return '<span class="skill-tag required">' + s.skill_name + '</span>'; }).join('') + '</div>' : '') +
          (preferred.length > 0 ?
              '<div style="margin-bottom:20px;"><h3 style="font-size:15px; font-weight:600; color:#1e293b; margin-bottom:10px;">Preferred Skills</h3>' +
              preferred.map(function (s) { return '<span class="skill-tag">' + s.skill_name + '</span>'; }).join('') + '</div>' : '') +
          '<div id="alert-apply" class="alert"></div>' +
          '<button class="btn btn-primary" style="width:100%; padding:14px;" ' +
          'onclick="applyForJob(' + jobId + ')">Apply for this Position</button>';
  } catch (err) {
      showAlert('alert-detail', 'Could not load job details.', 'error');
  }
}


async function applyForJob(jobId) {
  try {
      const res = await fetch(API + '/applications/apply', {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ job_id: jobId })
      });
      const data = await res.json();
      if (!res.ok) { showAlert('alert-apply', data.detail || 'Could not apply.', 'error'); return; }
      showAlert('alert-apply', data.message, 'success');
  } catch (err) {
      showAlert('alert-apply', 'Could not connect to server.', 'error');
  }
}

async function loadApplications() {
  try {
      const res = await fetch(API + '/applications/my', { headers: authHeaders() });
      const apps = await res.json();
      const tbody = document.getElementById('applications-body');
      if (apps.length === 0) {
          tbody.innerHTML =
              '<tr><td colspan="6" style="text-align:center; padding:40px; color:#64748b;">' +
              'You have not applied to any jobs yet. ' +
              '<a href="/student/jobs.html" style="color:#4f46e5; font-weight:600;">Browse Jobs</a>' +
              '</td></tr>';
          return;
      }
      tbody.innerHTML = apps.map(function (a) {
          const date = new Date(a.apply_date).toLocaleDateString('en-GB', {
              day: 'numeric', month: 'short', year: 'numeric'
          });
          const score = a.match_score != null
              ? '<div class="score-bar-wrap"><div class="score-bar"><div class="score-fill" style="width:' +
              a.match_score + '%;"></div></div><span class="score-text">' + a.match_score + '</span></div>'
              : '—';
          return '<tr>' +
              '<td><strong>' + a.job_title + '</strong></td>' +
              '<td>' + a.company_name + '</td>' +
              '<td>' + score + '</td>' +
              '<td>' + (a.rank_position != null ? '#' + a.rank_position : '—') + '</td>' +
              '<td><span class="badge badge-' + a.status + '">' + a.status + '</span></td>' +
              '<td>' + date + '</td>' +
              '</tr>';
      }).join('');
  } catch (err) {
      showAlert('alert-apps', 'Could not load applications.', 'error');
  }
}

async function loadRecommendations() {
  const el = document.getElementById('recommendations-grid');
  try {
      const res = await fetch(API + '/recommendations/', { headers: authHeaders() });
      const data = await res.json();
      if (!data.recommendations || data.recommendations.length === 0) {
          el.innerHTML =
              '<div class="card"><div class="empty-state">' +
              '<p>' + (data.message || 'No recommendations found.') + '</p>' +
              '<a href="/student/profile.html" class="btn btn-primary btn-sm">Complete Your Profile</a>' +
              '</div></div>';
          return;
      }
      el.innerHTML = data.recommendations.map(function (r, i) {
          const fit = parseFloat(r.rec_fit_score);
          const deadline = new Date(r.rec_deadline).toLocaleDateString('en-GB', {
              day: 'numeric', month: 'short', year: 'numeric'
          });
          return '<div class="card" style="margin-bottom:16px;">' +
              '<div style="display:flex; justify-content:space-between; align-items:flex-start;">' +
              '<div style="flex:1;">' +
              '<div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">' +
              '<span style="background:#4f46e5; color:white; width:26px; height:26px; border-radius:50%;' +
              'display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex-shrink:0;">' +
              (i + 1) + '</span>' +
              '<h3 style="font-size:16px; font-weight:700; color:#1e293b;">' + r.rec_title + '</h3>' +
              '</div>' +
              '<p style="font-size:13px; color:#64748b; margin-bottom:12px;">' +
              r.rec_company + ' · Deadline: ' + deadline +
              ' · Rs ' + Number(r.rec_salary).toLocaleString() + '</p>' +
              '<div class="score-bar-wrap">' +
              '<div class="score-bar" style="max-width:200px;">' +
              '<div class="score-fill" style="width:' + fit + '%; background:#16a34a;"></div>' +
              '</div>' +
              '<span style="font-size:13px; font-weight:700; color:#16a34a;">' + fit.toFixed(1) + '% match</span>' +
              '</div></div>' +
              '<a href="/student/job_detail.html?id=' + r.rec_job_id + '"' +
              ' class="btn btn-primary btn-sm" style="margin-left:16px; flex-shrink:0;">View Job</a>' +
              '</div></div>';
      }).join('');
  } catch (err) {
      if (el) el.innerHTML =
          '<div class="card"><div class="empty-state"><p>Could not load recommendations.</p></div></div>';
  }
}