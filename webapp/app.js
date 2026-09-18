const tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const CHECK_ICON =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

const SPARKLE_PATH = "M12 2 L14 10 L22 12 L14 14 L12 22 L10 14 L2 12 L10 10 Z";

// Иконка на бейдж по порогу дней — порядок соответствует STREAK_BADGE_THRESHOLDS в app/config.py.
const BADGE_ICONS = {
  3: '<path d="M12 20V11"/><path d="M12 11c0-3 2-5 5-5 0 3-2 5-5 5z"/><path d="M12 11c0-3-2-5-5-5 0 3 2 5 5 5z"/>',
  7: '<path d="M2 18h17a3 3 0 0 0 3-3c-3 0-5-1-7-3l-3-3c-1-1-2-1-3-1H6a2 2 0 0 0-2 2v3l-2 2z"/><path d="M7 18v-3"/><path d="M11 18v-3"/>',
  14: '<path d="M12 20c-4 0-7-3-7-7 3 0 5 1 7 3 2-2 4-3 7-3 0 4-3 7-7 7z"/><path d="M12 20V10"/><path d="M12 13c-2-2-2-5-2-7 2 1 3 3 4 5"/><path d="M12 13c2-2 2-5 2-7-2 1-3 3-4 5"/>',
  30: '<path d="M6 9h12l-6 12z"/><path d="M6 9l3-5h6l3 5"/><path d="M9 9l3-5 3 5"/>',
  60: '<path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 5H5a2 2 0 0 0 0 4h1"/><path d="M16 5h3a2 2 0 0 1 0 4h-1"/><path d="M12 13v3"/><path d="M9 20h6"/><path d="M10 16h4l1 4H9l1-4z"/>',
};

// Акцентный цвет каждой участницы — совпадает с CSS-переменными --accent
// для соответствующей темы в style.css, чтобы кольцо аватарки было её
// "фирменным" цветом независимо от темы, в которой сейчас открыт Mini App.
const THEME_ACCENT = {
  altana: "#3462ff",
  elya: "#ff2f7e",
  masha: "#8b5cf6",
};

function showError(message) {
  document.getElementById("loading").hidden = true;
  const errorEl = document.getElementById("error");
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function avatarUrl(telegramId) {
  return `/api/avatar/${telegramId}`;
}

function renderHello(name) {
  document.getElementById("hello-name").textContent = `Hi, ${name}`;
  document.getElementById("hello-date").textContent = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

function renderHero(personalStreak, nextBadge) {
  document.getElementById("hero-value").textContent = personalStreak;

  const progress = document.getElementById("hero-progress");
  if (!nextBadge) {
    progress.hidden = true;
    return;
  }
  progress.hidden = false;

  const prevThresholds = Object.keys(BADGE_ICONS)
    .map(Number)
    .filter((t) => t < nextBadge.threshold);
  const prev = prevThresholds.length ? Math.max(...prevThresholds) : 0;
  const span = nextBadge.threshold - prev;
  const pct = span > 0 ? Math.min(100, Math.max(0, ((personalStreak - prev) / span) * 100)) : 100;

  document.getElementById("hero-progress-fill").style.width = `${pct}%`;
  const dayWord = nextBadge.days_left === 1 ? "day" : "days";
  document.getElementById(
    "hero-progress-text"
  ).textContent = `${nextBadge.days_left} ${dayWord} to the "${nextBadge.threshold} days" badge`;
}

function renderGroupAvatars(participants) {
  const container = document.getElementById("group-avatars");
  container.innerHTML = "";
  participants.forEach((p) => {
    const el = document.createElement("div");
    el.className = "mini-avatar";
    el.style.backgroundColor = THEME_ACCENT[p.theme] || THEME_ACCENT.altana;
    el.style.backgroundImage = `url('${avatarUrl(p.telegram_id)}')`;
    el.textContent = p.name.charAt(0).toUpperCase();
    container.appendChild(el);
  });
}

function renderQuest(questToday) {
  const container = document.getElementById("quest-avatars");
  container.innerHTML = "";

  questToday.participants.forEach((p) => {
    const wrapper = document.createElement("div");
    wrapper.className = "quest-participant";

    const ring = THEME_ACCENT[p.theme] || THEME_ACCENT.altana;
    const avatar = document.createElement("div");
    avatar.className = "avatar" + (p.checked_in_today ? " checked" : "");
    avatar.style.setProperty("--ring", ring);
    avatar.textContent = p.name.charAt(0).toUpperCase();
    if (!p.checked_in_today) {
      avatar.style.opacity = "0.45";
    }

    // Фото профиля есть не всегда (например, участница ещё не выставила
    // аватар в Telegram) — грузим отдельно и переключаемся на неё, только
    // если запрос реально успешен, иначе остаётся буква как фолбэк.
    const img = new Image();
    img.onload = () => {
      avatar.classList.add("has-photo");
      avatar.style.backgroundImage = `url('${avatarUrl(p.telegram_id)}')`;
    };
    img.src = avatarUrl(p.telegram_id);

    if (p.checked_in_today) {
      const check = document.createElement("div");
      check.className = "avatar-check";
      check.innerHTML = CHECK_ICON;
      avatar.appendChild(check);
    }

    const name = document.createElement("span");
    name.className = "avatar-name" + (p.checked_in_today ? "" : " faint");
    name.textContent = p.name;

    wrapper.appendChild(avatar);
    wrapper.appendChild(name);
    container.appendChild(wrapper);
  });

  document.getElementById("quest-count").textContent = `${questToday.completed_count} of ${questToday.total}`;
}

function renderPlan(planToday) {
  document.getElementById("plan-title").textContent = `Today's Plan — ${planToday.day_name}`;
  const list = document.getElementById("plan-list");
  list.innerHTML = "";

  if (planToday.activities.length === 0) {
    const li = document.createElement("li");
    li.className = "plan-empty";
    li.textContent = "No plan set yet";
    list.appendChild(li);
    return;
  }

  planToday.activities.forEach((activity) => {
    const li = document.createElement("li");
    li.className = "plan-item" + (planToday.completed ? " done" : "");

    const check = document.createElement("span");
    check.className = "plan-check";
    check.innerHTML = CHECK_ICON;

    const label = document.createElement("span");
    label.textContent = activity;

    li.appendChild(check);
    li.appendChild(label);
    list.appendChild(li);
  });
}

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function renderCalendar(days) {
  const grid = document.getElementById("calendar-grid");
  const monthsRow = document.getElementById("calendar-months");
  grid.innerHTML = "";
  monthsRow.innerHTML = "";

  const todayIso = days.length ? days[days.length - 1].date : null;

  // Выравниваем по понедельникам, как в GitHub-heatmap: первая неделя может
  // содержать дни ДО начала диапазона — их просто оставляем пустыми ячейками.
  const first = new Date(days[0].date);
  const startDow = (first.getDay() + 6) % 7;
  const padded = Array.from({ length: startDow }, () => null).concat(days);

  let week = 0;
  let lastMonth = -1;
  const monthLabels = [];

  padded.forEach((day, i) => {
    const dow = i % 7;
    if (day) {
      const d = new Date(day.date);
      if (dow === 0 || i === 0) {
        if (d.getMonth() !== lastMonth) {
          monthLabels.push({ week, label: MONTH_NAMES[d.getMonth()] });
          lastMonth = d.getMonth();
        }
      }
    }

    const cell = document.createElement("div");
    cell.className = "cal-cell";
    if (day) {
      cell.className += day.checked ? " filled" : "";
      cell.className += day.date === todayIso ? " today" : "";
      cell.title = day.date;
    }
    grid.appendChild(cell);

    if (dow === 6) week++;
  });

  grid.style.gridTemplateColumns = `repeat(${week + 1}, 12px)`;
  monthLabels.forEach((m) => {
    const el = document.createElement("span");
    el.textContent = m.label;
    el.style.gridColumnStart = m.week + 1;
    monthsRow.appendChild(el);
  });
}

function renderBadges(badges, nextBadge) {
  const row = document.getElementById("badges-row");
  row.innerHTML = "";

  const unlockedThresholds = badges.filter((x) => x.unlocked).map((x) => x.threshold);

  badges.forEach((b) => {
    const el = document.createElement("div");
    el.className = "badge" + (b.unlocked ? " unlocked" : "");

    const icon = document.createElement("div");
    icon.className = "badge-icon";

    if (!b.unlocked && nextBadge && nextBadge.threshold === b.threshold) {
      el.classList.add("next");
      const prev = unlockedThresholds.length ? Math.max(...unlockedThresholds) : 0;
      const span = b.threshold - prev;
      const done = b.threshold - nextBadge.days_left - prev;
      const pct = span > 0 ? Math.min(100, Math.max(0, (done / span) * 100)) : 0;

      const ring = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      ring.setAttribute("class", "badge-ring");
      ring.setAttribute("viewBox", "0 0 36 36");
      ring.innerHTML = `
        <path class="ring-bg" d="M18 2 a16 16 0 1 1 0 32 a16 16 0 1 1 0 -32" />
        <path class="ring-fill" stroke-dasharray="${pct},100" d="M18 2 a16 16 0 1 1 0 32 a16 16 0 1 1 0 -32" />
      `;
      icon.appendChild(ring);
    }

    const tierSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    tierSvg.setAttribute("class", "tier-icon");
    tierSvg.setAttribute("viewBox", "0 0 24 24");
    tierSvg.innerHTML = BADGE_ICONS[b.threshold] || "";
    icon.appendChild(tierSvg);

    const sparkle = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    sparkle.setAttribute("class", "badge-sparkle");
    sparkle.setAttribute("viewBox", "0 0 24 24");
    sparkle.innerHTML = `<path d="${SPARKLE_PATH}"/>`;
    icon.appendChild(sparkle);

    const numRow = document.createElement("div");
    numRow.className = "badge-num-row";
    numRow.innerHTML = `<span class="badge-num">${b.threshold}</span><span class="badge-unit">days</span>`;
    icon.appendChild(numRow);

    const underline = document.createElement("div");
    underline.className = "badge-underline";
    icon.appendChild(underline);

    el.appendChild(icon);
    row.appendChild(el);
  });
}

function render(data) {
  document.getElementById("app").dataset.user = data.theme;

  renderHello(data.name);
  renderHero(data.personal_streak, data.next_badge);
  document.getElementById("group-value").textContent = data.group_streak;
  renderGroupAvatars(data.quest_today.participants);
  renderQuest(data.quest_today);
  renderPlan(data.plan_today);
  renderCalendar(data.calendar);
  renderBadges(data.badges, data.next_badge);

  document.getElementById("loading").hidden = true;
  document.getElementById("content").hidden = false;
}

async function loadDashboard() {
  const initData = tg ? tg.initData : "";

  if (!initData) {
    showError("Open the tracker via the button in the Telegram bot.");
    return;
  }

  try {
    const response = await fetch("/api/dashboard", {
      headers: { "X-Telegram-Init-Data": initData },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      showError(body.detail || "Couldn't load data.");
      return;
    }

    render(await response.json());
  } catch (err) {
    showError("No connection to the server.");
  }
}

loadDashboard();
