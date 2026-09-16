const tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const ICONS = {
  flame:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2c1.2 3.2-2.1 4.3-2.1 7.4a4.1 4.1 0 0 0 8.2 0c0-1-.4-1.9-1-2.8 1 3.8-1 6.4-3.1 6.4a3.1 3.1 0 0 1-3-3.5c0-2.3 2-3.3 1-7.5z"/></svg>',
  group:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  check:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  lock:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  award:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M8.7 13.6 7 22l5-3 5 3-1.7-8.4"/></svg>',
};

document.querySelectorAll(".streak-icon").forEach((el) => {
  el.innerHTML = ICONS[el.dataset.icon] || "";
});

function showError(message) {
  document.getElementById("loading").hidden = true;
  const errorEl = document.getElementById("error");
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function renderQuest(questToday) {
  const container = document.getElementById("quest-avatars");
  container.innerHTML = "";

  questToday.participants.forEach((p) => {
    const wrapper = document.createElement("div");
    wrapper.className = "quest-participant";

    const avatar = document.createElement("div");
    avatar.className = "avatar" + (p.checked_in_today ? " checked" : "");
    avatar.textContent = p.name.charAt(0).toUpperCase();

    if (p.checked_in_today) {
      const check = document.createElement("div");
      check.className = "avatar-check";
      check.innerHTML = ICONS.check;
      avatar.appendChild(check);
    }

    const name = document.createElement("span");
    name.className = "avatar-name";
    name.textContent = p.name;

    wrapper.appendChild(avatar);
    wrapper.appendChild(name);
    container.appendChild(wrapper);
  });

  document.getElementById("quest-count").textContent = `${questToday.completed_count} из ${questToday.total}`;
}

function renderPlan(planToday) {
  document.getElementById("plan-title").textContent = `План на сегодня — ${planToday.day_name}`;
  const list = document.getElementById("plan-list");
  list.innerHTML = "";

  if (planToday.activities.length === 0) {
    const li = document.createElement("li");
    li.className = "plan-empty";
    li.textContent = "План не задан";
    list.appendChild(li);
    return;
  }

  planToday.activities.forEach((activity) => {
    const li = document.createElement("li");
    li.className = "plan-item" + (planToday.completed ? " done" : "");

    const check = document.createElement("span");
    check.className = "plan-check";
    check.innerHTML = ICONS.check;

    const label = document.createElement("span");
    label.textContent = activity;

    li.appendChild(check);
    li.appendChild(label);
    list.appendChild(li);
  });
}

function renderCalendar(days) {
  const grid = document.getElementById("calendar-grid");
  grid.innerHTML = "";
  days.forEach((day) => {
    const cell = document.createElement("div");
    cell.className = "cal-cell" + (day.checked ? " filled" : "");
    cell.title = day.date;
    grid.appendChild(cell);
  });
}

function renderBadges(badges) {
  const row = document.getElementById("badges-row");
  row.innerHTML = "";
  badges.forEach((b) => {
    const el = document.createElement("div");
    el.className = "badge" + (b.unlocked ? " unlocked" : "");

    const icon = document.createElement("div");
    icon.className = "badge-icon";
    icon.innerHTML = b.unlocked ? ICONS.award : ICONS.lock;

    const label = document.createElement("span");
    label.className = "badge-label";
    label.textContent = `${b.threshold} дн.`;

    el.appendChild(icon);
    el.appendChild(label);
    row.appendChild(el);
  });
}

function render(data) {
  document.getElementById("personal-streak").textContent = data.personal_streak;
  document.getElementById("group-streak").textContent = data.group_streak;
  renderQuest(data.quest_today);
  renderPlan(data.plan_today);
  renderCalendar(data.calendar);
  renderBadges(data.badges);

  document.getElementById("loading").hidden = true;
  document.getElementById("content").hidden = false;
}

async function loadDashboard() {
  const initData = tg ? tg.initData : "";

  if (!initData) {
    showError("Открой трекер через кнопку в боте Telegram.");
    return;
  }

  try {
    const response = await fetch("/api/dashboard", {
      headers: { "X-Telegram-Init-Data": initData },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      showError(body.detail || "Не удалось загрузить данные.");
      return;
    }

    render(await response.json());
  } catch (err) {
    showError("Нет соединения с сервером.");
  }
}

loadDashboard();
