const DEFAULT_API_BASE = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? "http://127.0.0.1:8000"
  : window.location.origin;
let apiBase = DEFAULT_API_BASE;
let sessionId = localStorage.getItem("salescare.sessionId") || "";
let knowledgeItems = [];
let demoProducts = [];
let demoOrders = [];
let handoffTickets = [];
let sessionItems = [];

const $ = (selector) => document.querySelector(selector);
const messagesEl = $("#messages");
const statusDot = $("#statusDot");
const statusText = $("#statusText");
const sessionIdEl = $("#sessionId");

function isAdminMode() {
  return document.body.classList.contains("admin-mode");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const res = await fetch(`${apiBase}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || data.error || `HTTP ${res.status}`);
  }
  return data;
}

function setStatus(ok, text) {
  statusDot.classList.toggle("ok", ok);
  statusDot.classList.toggle("bad", !ok);
  statusText.textContent = text;
}

function updateSessionLabel() {
  sessionIdEl.textContent = sessionId ? sessionId : "未建立";
}

function switchAppMode(mode) {
  const admin = mode === "admin";
  document.body.classList.toggle("admin-mode", admin);
  document.body.classList.toggle("buyer-mode", !admin);
  if (admin) {
    switchTab("overview");
    renderAdminOverview();
  }
}

function renderEmptyState() {
  messagesEl.innerHTML = `
    <div class="welcome-card">
      <img src="assets/brand-mark.svg" alt="" />
      <p class="welcome-kicker">悦行售后客服</p>
      <h3>您好，欢迎来到悦行官方售后服务中心</h3>
      <p>我是智能客服小悦，可以帮您查询订单、处理退换货、排查故障、预约门店，也可以在需要时建议转人工客服。</p>
      <div class="welcome-options">
        <button class="message-action" data-question="1 产品咨询：我想了解悦行 S1 和 Pro 的区别">1 产品咨询</button>
        <button class="message-action" data-question="2 订单查询：我想查询订单进度">2 订单查询</button>
        <button class="message-action" data-question="3 退换货：我想了解七天无理由退换规则">3 退换货</button>
        <button class="message-action" data-question="4 故障排查：我的车无法启动，应该怎么排查？">4 故障排查</button>
        <button class="message-action" data-question="5 投诉升级：我很生气，维修太慢了，怎么处理？">5 投诉升级</button>
        <button class="message-action" data-question="6 转人工：我要联系人工客服">6 转人工</button>
      </div>
    </div>
  `;
}

function appendMessage(role, content, meta = {}) {
  const empty = messagesEl.querySelector(".welcome-card");
  if (empty) empty.remove();

  const isUser = role === "user";
  const wrapper = document.createElement("article");
  wrapper.className = `message ${isUser ? "user" : "assistant"}`;
  const metaParts = [];
  if (!isUser && meta.intent) metaParts.push(`意图：${meta.intent}`);
  if (!isUser && meta.model_mode) {
    const modeLabel = {
      deepseek: "DeepSeek",
      "local-retrieval": "本地检索",
      "order-workflow": "订单工作流",
      "human-handoff": "人工工单",
    }[meta.model_mode] || meta.model_mode;
    metaParts.push(modeLabel);
  }
  if (!isUser && meta.sources?.length) {
    metaParts.push(`来源：${meta.sources.map((item) => item.title).join("、")}`);
  }
  wrapper.innerHTML = `
    <div class="avatar">${isUser ? "客" : "AI"}</div>
    <div>
      <div class="bubble">${escapeHtml(content)}</div>
      ${
        metaParts.length
          ? `<div class="meta-row">${metaParts
              .map((item) => `<span class="meta-pill">${escapeHtml(item)}</span>`)
              .join("")}</div>`
          : ""
      }
    </div>
  `;
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function checkHealth() {
  try {
    await api("/api/health");
    setStatus(true, "后端已连接");
  } catch (err) {
    setStatus(false, "后端未连接");
  }
}

async function sendMessage(text) {
  appendMessage("user", text);
  const form = $("#chatForm");
  form.classList.add("loading");
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: text, session_id: sessionId || undefined }),
    });
    sessionId = data.session_id;
    localStorage.setItem("salescare.sessionId", sessionId);
    updateSessionLabel();
    appendMessage("assistant", data.answer, data);
    await Promise.all([loadSessions(), loadHandoffTickets()]);
    if (data.intent === "转人工" && isAdminMode()) {
      switchTab("handoff");
    }
  } catch (err) {
    appendMessage("assistant", `请求失败：${err.message}`);
  } finally {
    form.classList.remove("loading");
  }
}

async function loadKnowledge() {
  const list = $("#knowledgeList");
  list.innerHTML = "<p class=\"hint\">正在加载知识库...</p>";
  try {
    const data = await api("/api/knowledge");
    knowledgeItems = data.items;
    renderKnowledge();
  } catch (err) {
    list.innerHTML = `<p class="hint">知识库加载失败：${escapeHtml(err.message)}</p>`;
  }
}

function renderKnowledge() {
  const list = $("#knowledgeList");
  if (!knowledgeItems.length) {
    list.innerHTML = "<p class=\"hint\">暂无知识条目。</p>";
    return;
  }
  list.innerHTML = knowledgeItems
    .map(
      (item) => `
        <article class="kb-item">
          <h3>${escapeHtml(item.title)}</h3>
          <p><strong>${escapeHtml(item.category)}</strong> · ${escapeHtml(item.question)}</p>
          <p>${escapeHtml(item.answer)}</p>
          <div class="item-actions">
            <button class="secondary-action" data-edit-kb="${item.id}">编辑</button>
            <button class="danger-action" data-delete-kb="${item.id}">删除</button>
          </div>
        </article>
      `
    )
    .join("");
}

function fillKnowledgeForm(item) {
  $("#knowledgeId").value = item?.id || "";
  $("#kbCategory").value = item?.category || "";
  $("#kbTitle").value = item?.title || "";
  $("#kbQuestion").value = item?.question || "";
  $("#kbAnswer").value = item?.answer || "";
  $("#kbKeywords").value = item?.keywords || "";
}

async function saveKnowledge(event) {
  event.preventDefault();
  const id = $("#knowledgeId").value;
  const payload = {
    category: $("#kbCategory").value,
    title: $("#kbTitle").value,
    question: $("#kbQuestion").value,
    answer: $("#kbAnswer").value,
    keywords: $("#kbKeywords").value,
  };
  const path = id ? `/api/knowledge/${id}` : "/api/knowledge";
  const method = id ? "PUT" : "POST";
  try {
    await api(path, { method, body: JSON.stringify(payload) });
    fillKnowledgeForm(null);
    await loadKnowledge();
  } catch (err) {
    alert(`保存失败：${err.message}`);
  }
}

async function deleteKnowledge(id) {
  if (!confirm("确认删除这条知识库内容？")) return;
  try {
    await api(`/api/knowledge/${id}`, { method: "DELETE" });
    await loadKnowledge();
  } catch (err) {
    alert(`删除失败：${err.message}`);
  }
}

async function loadSessions() {
  const list = $("#sessionList");
  try {
    const data = await api("/api/sessions");
    sessionItems = data.items || [];
    if (!data.items.length) {
      list.innerHTML = "<p class=\"hint\">暂无会话。</p>";
      renderAdminOverview();
      return;
    }
    list.innerHTML = data.items
      .map(
        (item) => `
          <article class="session-item">
            <h3>${escapeHtml(item.id)}</h3>
            <p>${escapeHtml(item.last_user_message || "暂无用户消息")}</p>
            <p>${item.message_count} 条消息 · ${escapeHtml(item.updated_at)}</p>
          </article>
        `
      )
      .join("");
    renderAdminOverview();
  } catch (err) {
    list.innerHTML = `<p class="hint">会话加载失败：${escapeHtml(err.message)}</p>`;
  }
}

function orderSummary(order) {
  return `${order.order_no} · ${order.product_name} · ${order.status}`;
}

async function loadOrders() {
  const list = $("#orderList");
  list.innerHTML = "<p class=\"hint\">正在加载演示订单...</p>";
  try {
    const data = await api("/api/demo-orders");
    demoProducts = data.products || [];
    demoOrders = data.items || [];
    renderProductSelect();
    renderOrders();
    renderAdminOverview();
  } catch (err) {
    list.innerHTML = `<p class="hint">订单加载失败：${escapeHtml(err.message)}</p>`;
  }
}

function renderProductSelect() {
  const select = $("#demoProductSelect");
  if (!select) return;
  select.innerHTML = demoProducts
    .map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`)
    .join("");
}

function renderOrders() {
  const list = $("#orderList");
  if (!demoOrders.length) {
    list.innerHTML = "<p class=\"hint\">暂无演示订单。</p>";
    return;
  }
  list.innerHTML = demoOrders
    .map(
      (order) => `
        <article class="order-item">
          <div class="order-head">
            <h3>${escapeHtml(order.order_no)}</h3>
            <span>${escapeHtml(order.status)}</span>
          </div>
          <p>${escapeHtml(order.product_name)} · ${escapeHtml(order.city)} · ${Number(order.amount).toFixed(2)} 元</p>
          <p>买家：${escapeHtml(order.customer_name || "演示客户")} · 付款：${escapeHtml(order.payment_status || "已支付")}</p>
          <p>${escapeHtml(order.logistics_status)}</p>
          <div class="item-actions">
            <button class="secondary-action" data-send-order="${escapeHtml(order.order_no)}">发送订单号</button>
          </div>
        </article>
      `
    )
    .join("");
}

async function createDemoOrder() {
  const productName = $("#demoProductSelect")?.value || "";
  try {
    const data = await api("/api/demo-orders/create", {
      method: "POST",
      body: JSON.stringify({ product_name: productName }),
    });
    await loadOrders();
    renderAdminOverview();
    switchTab("orders");
    appendMessage(
      "assistant",
      `已生成一笔课堂演示订单：${orderSummary(data.item)}\n\n您可以把订单号 ${data.item.order_no} 发给我，我会返回付款、物流、售后处理状态。`,
      { intent: "订单查询", model_mode: "order-workflow" }
    );
  } catch (err) {
    appendMessage("assistant", `生成演示订单失败：${err.message}`);
  }
}

async function loadHandoffTickets() {
  const list = $("#ticketList");
  list.innerHTML = "<p class=\"hint\">正在加载人工工单...</p>";
  try {
    const data = await api("/api/handoff-tickets");
    handoffTickets = data.items || [];
    renderHandoffTickets();
    renderAdminOverview();
  } catch (err) {
    list.innerHTML = `<p class="hint">工单加载失败：${escapeHtml(err.message)}</p>`;
  }
}

function renderHandoffTickets() {
  const list = $("#ticketList");
  if (!handoffTickets.length) {
    list.innerHTML = "<p class=\"hint\">暂无人工工单。点击“转人工”后，这里会出现工单记录。</p>";
    return;
  }
  list.innerHTML = handoffTickets
    .map(
      (ticket) => `
        <article class="ticket-item">
          <div class="ticket-head">
            <h3>${escapeHtml(ticket.ticket_no)}</h3>
            <span>${escapeHtml(ticket.status)}</span>
          </div>
          <p>${escapeHtml(ticket.assigned_team)} · 优先级 ${escapeHtml(ticket.priority)}</p>
          <p>${escapeHtml(ticket.reason)}</p>
          <p>${escapeHtml(ticket.expected_response)} · ${escapeHtml(ticket.updated_at)}</p>
        </article>
      `
    )
    .join("");
}

function formatMoney(value) {
  return Number(value || 0).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function countBy(items, key) {
  return items.reduce((acc, item) => {
    const label = item[key] || "未分类";
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {});
}

function renderCountSummary(title, counts) {
  const entries = Object.entries(counts);
  if (!entries.length) return `<div class="summary-row"><strong>${title}</strong><span>暂无数据</span></div>`;
  return `
    <div class="summary-row">
      <strong>${title}</strong>
      <span>${entries.map(([name, count]) => `${escapeHtml(name)} ${count} 单`).join(" · ")}</span>
    </div>
  `;
}

function renderAdminOverview() {
  const summaryGrid = $("#summaryGrid");
  const buyerOrderTable = $("#buyerOrderTable");
  const orderSummaryList = $("#orderSummaryList");
  if (!summaryGrid || !buyerOrderTable || !orderSummaryList) return;

  const totalAmount = demoOrders.reduce((sum, order) => sum + Number(order.amount || 0), 0);
  const activeTickets = handoffTickets.filter((ticket) => ticket.status !== "已完成").length;
  const aftersaleOrders = demoOrders.filter((order) => String(order.aftersale_status || "").includes("售后")).length;

  summaryGrid.innerHTML = [
    ["订单总数", `${demoOrders.length} 单`],
    ["演示成交额", `${formatMoney(totalAmount)} 元`],
    ["售后相关订单", `${aftersaleOrders} 单`],
    ["待处理工单", `${activeTickets} 单`],
    ["会话数量", `${sessionItems.length} 个`],
  ]
    .map(
      ([label, value]) => `
        <article class="summary-card">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>
      `
    )
    .join("");

  if (!demoOrders.length) {
    buyerOrderTable.innerHTML = "<p class=\"hint\">暂无买家订单。</p>";
  } else {
    buyerOrderTable.innerHTML = `
      <table class="admin-table">
        <thead>
          <tr>
            <th>订单号</th>
            <th>买家</th>
            <th>商品</th>
            <th>城市</th>
            <th>金额</th>
            <th>订单状态</th>
            <th>售后状态</th>
          </tr>
        </thead>
        <tbody>
          ${demoOrders
            .map(
              (order) => `
                <tr>
                  <td>${escapeHtml(order.order_no)}</td>
                  <td>${escapeHtml(order.customer_name || "演示客户")}</td>
                  <td>${escapeHtml(order.product_name)}</td>
                  <td>${escapeHtml(order.city)}</td>
                  <td>${formatMoney(order.amount)}</td>
                  <td>${escapeHtml(order.status)}</td>
                  <td>${escapeHtml(order.aftersale_status)}</td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  orderSummaryList.innerHTML = [
    renderCountSummary("按订单状态汇总", countBy(demoOrders, "status")),
    renderCountSummary("按商品汇总", countBy(demoOrders, "product_name")),
    renderCountSummary("按城市汇总", countBy(demoOrders, "city")),
    renderCountSummary("按售后状态汇总", countBy(demoOrders, "aftersale_status")),
  ].join("");
}

function switchTab(tabName) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  });
  document.querySelectorAll(".tab-page").forEach((page) => {
    page.classList.toggle("active", page.id === `${tabName}Tab`);
  });
}

function bindEvents() {
  $("#adminViewBtn").addEventListener("click", () => switchAppMode("admin"));
  $("#buyerViewBtn").addEventListener("click", () => switchAppMode("buyer"));

  $("#chatForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const input = $("#messageInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendMessage(text);
  });

  $("#messageInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("#chatForm").requestSubmit();
    }
  });

  $("#handoffBtn").addEventListener("click", () => {
    sendMessage("6 转人工：我要联系人工客服");
  });

  document.querySelectorAll(".quick-question").forEach((button) => {
    button.addEventListener("click", () => {
      sendMessage(button.dataset.question);
    });
  });

  document.querySelectorAll(".service-chip").forEach((button) => {
    button.addEventListener("click", () => {
      sendMessage(button.dataset.question);
    });
  });

  messagesEl.addEventListener("click", (event) => {
    const button = event.target.closest(".message-action");
    if (button?.dataset.question) {
      sendMessage(button.dataset.question);
    }
  });

  $("#newSessionBtn").addEventListener("click", () => {
    sessionId = "";
    localStorage.removeItem("salescare.sessionId");
    updateSessionLabel();
    renderEmptyState();
  });

  $("#knowledgeForm").addEventListener("submit", saveKnowledge);
  $("#resetKnowledgeBtn").addEventListener("click", () => fillKnowledgeForm(null));

  $("#knowledgeList").addEventListener("click", (event) => {
    const editId = event.target.dataset.editKb;
    const deleteId = event.target.dataset.deleteKb;
    if (editId) {
      const item = knowledgeItems.find((entry) => String(entry.id) === String(editId));
      fillKnowledgeForm(item);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (deleteId) deleteKnowledge(deleteId);
  });

  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });

  $("#createOrderBtn").addEventListener("click", createDemoOrder);
  $("#refreshOrdersBtn").addEventListener("click", loadOrders);
  $("#refreshOverviewBtn").addEventListener("click", async () => {
    await Promise.all([loadOrders(), loadSessions(), loadHandoffTickets()]);
    renderAdminOverview();
  });
  $("#orderList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-send-order]");
    if (button) {
      sendMessage(`查询订单 ${button.dataset.sendOrder}`);
    }
  });

  $("#createHandoffBtn").addEventListener("click", () => {
    sendMessage("6 转人工：我要联系人工客服");
  });
  $("#refreshHandoffBtn").addEventListener("click", loadHandoffTickets);
}

async function init() {
  updateSessionLabel();
  renderEmptyState();
  bindEvents();
  await checkHealth();
  await loadKnowledge();
  await loadSessions();
  await loadOrders();
  await loadHandoffTickets();
}

init();
