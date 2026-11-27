(function () {
  const article = document.querySelector("article");
  const toc = document.querySelector("#toc-links");
  const copyLabel = document.body.dataset.copy || "Copy";
  const copiedLabel = document.body.dataset.copied || "Copied";

  if (article && toc) {
    const heads = article.querySelectorAll("h2, h3");
    heads.forEach(function (head) {
      if (!head.id) {
        head.id = head.textContent
          .trim()
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
      }
      const link = document.createElement("a");
      link.href = "#" + head.id;
      link.textContent = head.textContent;
      if (head.tagName === "H3") link.className = "h3";
      toc.appendChild(link);
    });
    if (!heads.length) {
      const box = document.querySelector(".toc");
      if (box) box.hidden = true;
    }
  }

  if (article) {
    article.querySelectorAll("pre").forEach(function (pre) {
      const wrap = document.createElement("div");
      wrap.className = "code";
      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(pre);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "copy";
      button.textContent = copyLabel;
      button.addEventListener("click", function () {
        const text = pre.innerText;
        navigator.clipboard.writeText(text).then(function () {
          button.textContent = copiedLabel;
          setTimeout(function () { button.textContent = copyLabel; }, 1200);
        });
      });
      wrap.appendChild(button);
    });

    article.querySelectorAll("table").forEach(function (table) {
      if (table.parentElement.classList.contains("table-wrap")) return;
      const wrap = document.createElement("div");
      wrap.className = "table-wrap";
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);
    });
  }

  const dialog = document.createElement("dialog");
  dialog.className = "zoom";
  const zoomImg = document.createElement("img");
  dialog.appendChild(zoomImg);
  dialog.addEventListener("click", function () { dialog.close(); });
  document.body.appendChild(dialog);
  document.querySelectorAll("figure.shot img").forEach(function (img) {
    img.addEventListener("click", function () {
      zoomImg.src = img.src;
      zoomImg.alt = img.alt;
      dialog.showModal();
    });
  });

  const input = document.querySelector("#q");
  const results = document.querySelector("#search-results");
  const index = window.WIKI_SEARCH || [];

  function fold(value) {
    return (value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function renderSearch(query) {
    const needle = fold(query.trim());
    results.innerHTML = "";
    if (!needle) {
      results.style.display = "none";
      return;
    }
    const hits = index.filter(function (item) {
      return fold(item.title + " " + item.text).indexOf(needle) !== -1;
    }).slice(0, 8);
    if (!hits.length) {
      results.style.display = "none";
      return;
    }
    hits.forEach(function (item) {
      const link = document.createElement("a");
      link.href = item.href;
      link.innerHTML = item.title + "<em>" + item.group + "</em>";
      results.appendChild(link);
    });
    results.style.display = "block";
  }

  if (input) {
    input.addEventListener("input", function () { renderSearch(input.value); });
    document.addEventListener("keydown", function (event) {
      if (event.key === "/" && document.activeElement !== input) {
        event.preventDefault();
        input.focus();
      }
      if (event.key === "Escape") {
        results.style.display = "none";
        document.body.classList.remove("nav-open");
      }
    });
    document.addEventListener("click", function (event) {
      if (!event.target.closest(".search")) results.style.display = "none";
    });
  }

  const menu = document.querySelector("#nav-toggle");
  if (menu) {
    menu.addEventListener("click", function () {
      document.body.classList.toggle("nav-open");
    });
    document.querySelectorAll(".sidebar a").forEach(function (link) {
      link.addEventListener("click", function () {
        document.body.classList.remove("nav-open");
      });
    });
  }
})();
