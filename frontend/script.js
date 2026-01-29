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

/* CUSTOM RULES LOGIC */
const ruleInput = document.getElementById('rule-input');
const addRuleBtn = document.getElementById('add-rule-btn');
const rulesGrid = document.getElementById('rules-grid');

// Function to create a delete button
function createDeleteBtn() {
  const btn = document.createElement('button');
  btn.innerHTML = '&times;';
  btn.className = 'delete-btn';
  btn.setAttribute('aria-label', 'Delete rule');
  return btn;
}

// Add delete buttons to existing static rules
document.querySelectorAll('.card').forEach(card => {
  // Check if it's inside the rules grid to avoid affecting other cards (like features/pricing) if class names overlap
  if (card.parentElement && card.parentElement.id === 'rules-grid') {
    card.appendChild(createDeleteBtn());
  }
});

// Add Rule Function
function addRule() {
  const text = ruleInput.value.trim();
  if (!text) return;

  const card = document.createElement('div');
  card.className = 'card';
  card.textContent = text;

  card.appendChild(createDeleteBtn());

  rulesGrid.appendChild(card);
  ruleInput.value = '';
}

// Event Listeners
if (addRuleBtn) {
  addRuleBtn.addEventListener('click', addRule);
}

if (ruleInput) {
  ruleInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addRule();
  });
}

// Event Delegation for Delete (handles both static and dynamic items)
if (rulesGrid) {
  rulesGrid.addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-btn')) {
      e.target.parentElement.remove();
    }
  });
}