const c = document.getElementById("particles");
const ctx = c.getContext("2d");

c.width = innerWidth;
c.height = innerHeight;

let dots = [];
for (let i = 0; i < 35; i++) {
  dots.push({
    x: Math.random() * c.width,
    y: Math.random() * c.height,
    r: 1 + Math.random() * 2,
    dx: (Math.random() - .5) * 0.6,
    dy: (Math.random() - .5) * 0.6
  })
}

function animate() {
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.fillStyle = "rgba(255,255,255,.8)";

  dots.forEach(d => {
    ctx.beginPath();
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
    ctx.fill();

    d.x += d.dx;
    d.y += d.dy;

    if (d.x < 0 || d.x > c.width) d.dx *= -1;
    if (d.y < 0 || d.y > c.height) d.dy *= -1;
  });

  requestAnimationFrame(animate);
}
animate();

addEventListener("resize", () => {
  c.width = innerWidth;
  c.height = innerHeight;
});

/* ================= FIX ADDED ================= */
const ruleInput = document.getElementById("ruleInput");
const rulesGrid = document.getElementById("rules-grid");
/* =========================================== */

const API_BASE_URL = 'http://localhost:8000/api/v1';
const BACKEND_BASE_URL = 'http://localhost:8000';
let currentApiKey = localStorage.getItem('myelin_api_key') || null;
let demoApiKeyCopied = sessionStorage.getItem('myelin_demo_key_copied') === 'true';

function ensureToastHost() {
  let host = document.getElementById('backend-toast-host');
  if (host) {
    return host;
  }

  host = document.createElement('div');
  host.id = 'backend-toast-host';
  host.style.position = 'fixed';
  host.style.right = '20px';
  host.style.bottom = '20px';
  host.style.zIndex = '9999';
  host.style.display = 'flex';
  host.style.flexDirection = 'column';
  host.style.gap = '10px';
  document.body.appendChild(host);
  return host;
}

function showToast(message, tone = 'info') {
  const host = ensureToastHost();
  const toast = document.createElement('div');
  toast.textContent = message;
  toast.style.maxWidth = '340px';
  toast.style.padding = '12px 16px';
  toast.style.borderRadius = '14px';
  toast.style.boxShadow = '0 18px 40px rgba(0, 0, 0, 0.35)';
  toast.style.backdropFilter = 'blur(8px)';
  toast.style.border = '1px solid rgba(255,255,255,0.18)';
  toast.style.color = '#eef3fa';
  toast.style.background = tone === 'error'
    ? 'rgba(120, 25, 35, 0.92)'
    : tone === 'success'
      ? 'rgba(18, 95, 82, 0.92)'
      : 'rgba(18, 24, 33, 0.92)';
  host.appendChild(toast);
  window.setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(6px)';
    toast.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
  }, 2600);
  window.setTimeout(() => toast.remove(), 3000);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch (_error) {
    data = { detail: text };
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || `HTTP ${response.status}`;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return data;
}

function openBackendPage(path) {
  window.open(`${BACKEND_BASE_URL}${path}`, '_blank', 'noopener,noreferrer');
}

function maskApiKey(value) {
  if (!value || value.length <= 12) {
    return value || '';
  }

  return `${value.slice(0, 20)}...${value.slice(-4)}`;
}

async function createDemoApiKey() {
  const payload = {
    full_name: 'Myelin Web Demo',
    organization_name: 'Myelin Demo Org'
  };

  try {
    const data = await fetchJson(`${BACKEND_BASE_URL}/api/v1/public/demo-api-key`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (data?.api_key) {
      currentApiKey = data.api_key;
      localStorage.setItem('myelin_api_key', data.api_key);

      if (!demoApiKeyCopied) {
        try {
          await navigator.clipboard.writeText(data.api_key);
          demoApiKeyCopied = true;
          sessionStorage.setItem('myelin_demo_key_copied', 'true');
        } catch (_error) {
          // Clipboard is optional; key is still stored locally.
        }
      }

      showToast(`API key created: ${data.api_key}`, 'success');
      return;
    }

    showToast('Backend responded, but no API key was returned.', 'error');
  } catch (error) {
    if (String(error.message || '').includes('disabled')) {
      showToast('Demo API key is disabled on the backend. Use the auth/register flow instead.', 'error');
      window.open(`${BACKEND_BASE_URL}/`, '_blank', 'noopener,noreferrer');
      return;
    }

    showToast(`API key request failed: ${error.message}`, 'error');
  }
}

async function pingBackendHealth() {
  try {
    const data = await fetchJson(`${BACKEND_BASE_URL}/health`, { method: 'GET' });
    showToast(`Backend ${data.status} | DB: ${data.database}`, 'success');
  } catch (error) {
    showToast(`Backend health check failed: ${error.message}`, 'error');
  }
}

/* ================= DOWNLOAD FIX ================= */

function handleDownload(e) {
    e.preventDefault();

    var btn = document.getElementById("downloadBtn");
    if (!btn) return;

    var orig = btn.innerHTML;
    btn.innerHTML = "Preparing… ⏳";
    btn.style.opacity = "0.7";
    btn.style.pointerEvents = "none";

    setTimeout(function () {

        var content = [
            "Myelin – AI Governance & Alignment Auditor",
            "==========================================",
            "",
            "Core Features:",
            "  • Toxicity & Safety Verification",
            "  • Factual Consistency Checking",
            "  • Fairness Analysis",
            "  • Bias Detection",
            "  • Alignment & Governance Reporting",
            "",
            "Generated: " + new Date().toLocaleString(),
        ].join("\n");   // ✅ FIXED HERE

        var blob = new Blob([content], { type: "text/plain" });
        var url  = URL.createObjectURL(blob);

        var a = document.createElement("a");
        a.href = url;
        a.download = "myelin-report.txt";

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        URL.revokeObjectURL(url);

        btn.innerHTML = orig;
        btn.style.opacity = "1";
        btn.style.pointerEvents = "auto";

    }, 800);
}

let currentSlideIndex = 0;

function updateSliderUI() {
  const slider = document.querySelector('.slider');
  const dots = document.querySelectorAll('.dot');

  if (slider) {
    slider.style.transform = "translateX(-" + (currentSlideIndex * 100) + "%)";
  }

  dots.forEach((dot, index) => {
    dot.classList.toggle('active', index === currentSlideIndex);
  });
}

function moveSlide(direction) {
  const slides = document.querySelectorAll('.slide');

  if (slides.length === 0) return;

  currentSlideIndex += direction;

  if (currentSlideIndex < 0) {
    currentSlideIndex = slides.length - 1;
  } else if (currentSlideIndex >= slides.length) {
    currentSlideIndex = 0;
  }

  updateSliderUI();
}

function currentSlide(slideNumber) {
  const slides = document.querySelectorAll('.slide');
  if (slides.length === 0) return;

  currentSlideIndex = Math.max(0, Math.min(slides.length - 1, slideNumber - 1));
  updateSliderUI();
}

// Make currentSlide available for existing inline onclick handlers.
window.currentSlide = currentSlide;
window.moveSlide = moveSlide;

document.addEventListener('DOMContentLoaded', function () {
  updateSliderUI();

  document.querySelectorAll('[data-backend-action]').forEach((element) => {
    element.addEventListener('click', async (event) => {
      const action = element.getAttribute('data-backend-action');
      if (!action) {
        return;
      }

      event.preventDefault();

      if (action === 'open-docs') {
        openBackendPage('/docs');
        showToast('Opening backend docs.', 'success');
        return;
      }

      if (action === 'open-root') {
        openBackendPage('/');
        showToast('Opening backend root endpoint.', 'success');
        return;
      }

      if (action === 'generate-demo-key') {
        await createDemoApiKey();
        return;
      }

      if (action === 'health-ping') {
        await pingBackendHealth();
        document.getElementById('features')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }

      if (action === 'scroll-to-api') {
        document.getElementById('api-access')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
    });
  });

  document.querySelectorAll('.slider-btn, .dot').forEach((element) => {
    element.addEventListener('click', () => {
      window.setTimeout(() => {
        pingBackendHealth();
      }, 50);
    });
  });

  const sliderContainer = document.querySelector('.slider-container');
  if (!sliderContainer) return;

  let autoSlide = setInterval(function () {
    moveSlide(1);
  }, 7000);

  sliderContainer.addEventListener('mouseenter', function () {
    clearInterval(autoSlide);
  });

  sliderContainer.addEventListener('mouseleave', function () {
    autoSlide = setInterval(function () {
      moveSlide(1);
    }, 7000);
  });
});