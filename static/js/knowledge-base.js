document.addEventListener("DOMContentLoaded", () => {
  const content = document.querySelector("[data-article-content]");
  const toc = document.querySelector("[data-article-toc]");
  if (!content || !toc) return;

  const headings = [...content.querySelectorAll("h2, h3")];
  if (!headings.length) {
    toc.innerHTML = "<span>В статье нет разделов</span>";
    return;
  }

  toc.innerHTML = "";
  headings.forEach((heading, index) => {
    const id = heading.id || `razdel-${index + 1}`;
    heading.id = id;
    const link = document.createElement("a");
    link.href = `#${id}`;
    link.textContent = heading.textContent;
    if (heading.tagName === "H3") link.classList.add("is-subsection");
    toc.appendChild(link);
  });
});
