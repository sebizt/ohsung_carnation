/* 동적 선생님 목록 로드, 검색, 선택 기능 */

// 글자 크기를 container 폭에 맞춰 자동 조절
function adjustFontSize(el, maxFont = 16, minFont = 12) {
  let fs = maxFont;
  el.style.fontSize = fs + 'px';
  // 스크롤폭이 container 폭을 넘으면 1px씩 줄인다
  while (el.scrollWidth > el.clientWidth && fs > minFont) {
    fs--;
    el.style.fontSize = fs + 'px';
  }
}

(async () => {
  const res = await fetch('/api/teachers');
  if (!res.ok) {
    alert('선생님 목록을 불러오는 중 오류가 발생했습니다');
    return;
  }
  const teachers = await res.json();
  const listEl = document.getElementById('teacherList');

  teachers.forEach(t => {
    const card = document.createElement('div');
    card.className = 'teacher-card';
    card.dataset.id = t.teacher_id;

    // teacher_id % 3 에 따라 프로필 선택
    let imgPath;
    const r = t.teacher_id % 3;
    if (r === 1) imgPath = '/static/assets/profile_1.png';
    else if (r === 2) imgPath = '/static/assets/profile_2.png';
    else /* r===0 */ imgPath = '/static/assets/profile_3.png';

    card.innerHTML = `
      <div class="avatar">
        <img src="${imgPath}" alt="${t.name} 프로필"
             style="width:100%; height:100%; object-fit:cover; border-radius:50%;">
      </div>
      <div class="info">
        <div class="name-row">
          <span class="name">${t.name}</span>
        </div>
        <p class="desc">${t.bio}</p>
      </div>
    `;

    card.addEventListener('click', () => {
      window.location.href = `/letters/${t.teacher_id}`;
    });

    listEl.appendChild(card);
  });

  // 검색 기능
  document.getElementById('search').addEventListener('input', e => {
    const kw = e.target.value.trim().toLowerCase();
    document.querySelectorAll('.teacher-card').forEach(card => {
      const name = card.querySelector('.name').textContent.toLowerCase();
      card.style.display = name.includes(kw) ? 'flex' : 'none';
    });
  });
})();


asdff = document.getElementById("Header");

asdfff = document.getElementById("teacherList");
asdffff = document.getElementById("content");

asdfff.style.height = asdffff.offsetHeight-asdfff.offsetHeight-85 + "px";