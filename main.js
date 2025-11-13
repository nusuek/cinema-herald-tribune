async function loadNews() {
  try {
    const res = await fetch('data/news.json');
    const data = await res.json();

    renderTopStories(data.top_stories || []);
    renderSectionLists(data);
  } catch (e) {
    console.error('ニュースの読み込みに失敗しました', e);
  }
}

function renderTopStories(stories) {
  const container = document.getElementById('top-stories-list');
  container.innerHTML = '';

  if (stories.length === 0) {
    container.textContent = 'No top stories.';
    return;
  }

  const [main, ...rest] = stories;

  if (main) {
    const mainEl = document.createElement('article');
    mainEl.className = 'top-story-main';
    mainEl.innerHTML = `
      <h3 class="top-story-main-title">
        <a href="${main.url}" target="_blank" rel="noopener" class="news-item-link">
          ${main.title}
        </a>
      </h3>
      <p class="top-story-meta">— ${main.source}｜${main.date}</p>
    `;
    container.appendChild(mainEl);
  }

  rest.forEach((story) => {
    const sideEl = document.createElement('article');
    sideEl.className = 'top-story-side';
    sideEl.innerHTML = `
      <p class="news-item-title">
        <a href="${story.url}" target="_blank" rel="noopener" class="news-item-link">
          ${story.title}
        </a>
      </p>
      <p class="top-story-meta">— ${story.source}｜${story.date}</p>
    `;
    container.appendChild(sideEl);
  });
}

function renderSectionLists(data) {
  const sections = document.querySelectorAll('.news-list');

  sections.forEach((ul) => {
    const sectionKey = ul.getAttribute('data-section'); // 例: "new_releases"
    const items = data[sectionKey] || [];
    ul.innerHTML = '';

    if (items.length === 0) {
      const li = document.createElement('li');
      li.className = 'news-item';
      li.textContent = 'No news.';
      ul.appendChild(li);
      return;
    }

    items.forEach((item) => {
      const li = document.createElement('li');
      li.className = 'news-item';

      // BDだけ release_date を一行目に出す
      let dateLine = '';
      if (sectionKey === 'bd_releases' && item.release_date) {
        dateLine = `${item.release_date}　`;
      }

      li.innerHTML = `
        <p class="news-item-title">
          ${dateLine}
          <a href="${item.url}" target="_blank" rel="noopener" class="news-item-link">
            ${item.title}
          </a>
        </p>
        <p class="news-item-meta">— ${item.source}｜${item.date}</p>
      `;
      ul.appendChild(li);
    });
  });
}

document.addEventListener('DOMContentLoaded', loadNews);
