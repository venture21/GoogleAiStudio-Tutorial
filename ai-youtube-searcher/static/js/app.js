// Tailwind CSS Custom Configuration
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        yt: {
          black: '#0f0f0f',
          dark: '#181818',
          card: '#212121',
          border: '#303030',
          hover: '#272727',
          red: '#ff0000',
          text: '#f1f1f1',
          muted: '#aaaaaa'
        }
      }
    }
  }
};

// Global State
let ytPlayer = null;
let isPlayerReady = false;
let currentVideoData = null;
let currentTranscriptData = null;
let currentSegments = [];
let isMuted = false;
let currentVolume = 100;
let playbackInterval = null;

// YouTube IFrame API Callback
window.onYouTubeIframeAPIReady = function () {
  console.log("YouTube IFrame API Ready");
};

// Jump to timestamp in seconds & Play
window.jumpToSeconds = function (seconds) {
  if (ytPlayer && ytPlayer.seekTo) {
    console.log(`Jumping to ${seconds} seconds...`);
    ytPlayer.seekTo(seconds, true);
    ytPlayer.playVideo();
  }
};

// Tab Switching
window.switchTab = function (tabName) {
  const tabs = ['search', 'timeline', 'qa'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const content = document.getElementById(`tab-content-${t}`);
    if (t === tabName) {
      btn.classList.add('border-red-500', 'text-white');
      btn.classList.remove('border-transparent', 'text-yt-muted');
      content.classList.remove('hidden');
    } else {
      btn.classList.remove('border-red-500', 'text-white');
      btn.classList.add('border-transparent', 'text-yt-muted');
      content.classList.add('hidden');
    }
  });
  lucide.createIcons();
};

document.addEventListener('DOMContentLoaded', () => {
  // Lucide Icons Render
  lucide.createIcons();

  // Elements
  const searchForm = document.getElementById('search-form');
  const urlInput = document.getElementById('url-input');
  const searchBtn = document.getElementById('search-btn');
  const aiStatusBadge = document.getElementById('ai-status-badge');
  const aiStatusText = document.getElementById('ai-status-text');
  const placeholder = document.getElementById('player-placeholder');
  const videoInfoCard = document.getElementById('video-info-card');
  const videoTitle = document.getElementById('video-title');
  const videoUploader = document.getElementById('video-uploader');
  const videoDuration = document.getElementById('video-duration');
  const volumeSlider = document.getElementById('volume-slider');
  const volumeVal = document.getElementById('volume-val');
  const volumeIcon = document.getElementById('volume-icon');
  const muteBtn = document.getElementById('mute-btn');
  const currentTimeDisplay = document.getElementById('current-time-display');

  const contentSearchInput = document.getElementById('content-search-input');
  const searchResultsList = document.getElementById('search-results-list');
  const timelineList = document.getElementById('timeline-list');
  const copyTranscriptBtn = document.getElementById('copy-transcript-btn');

  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatMessages = document.getElementById('chat-messages');
  const chatSubmitBtn = document.getElementById('chat-submit-btn');

  function initOrLoadVideo(videoId) {
    if (!ytPlayer) {
      ytPlayer = new YT.Player('yt-player', {
        videoId: videoId,
        playerVars: {
          playsinline: 1,
          autoplay: 1,
          controls: 1,
          rel: 0,
        },
        events: {
          onReady: (event) => {
            isPlayerReady = true;
            event.target.setVolume(currentVolume);
            event.target.playVideo();
            startTrackingTime();
          },
          onStateChange: () => {
            // state change hooks if needed
          }
        }
      });
    } else {
      ytPlayer.loadVideoById(videoId);
    }
    placeholder.classList.add('hidden');
  }

  // Time Tracking Loop
  function startTrackingTime() {
    if (playbackInterval) clearInterval(playbackInterval);
    playbackInterval = setInterval(() => {
      if (ytPlayer && ytPlayer.getCurrentTime && ytPlayer.getDuration) {
        try {
          const current = ytPlayer.getCurrentTime() || 0;
          const duration = ytPlayer.getDuration() || 0;
          currentTimeDisplay.textContent = `${formatSeconds(current)} / ${formatSeconds(duration)}`;
        } catch (e) { }
      }
    }, 500);
  }

  function formatSeconds(secs) {
    const s = Math.floor(secs);
    const m = Math.floor(s / 60);
    const remSec = s % 60;
    return `${m < 10 ? '0' : ''}${m}:${remSec < 10 ? '0' : ''}${remSec}`;
  }

  // Volume Slider & Mute
  volumeSlider.addEventListener('input', (e) => {
    currentVolume = parseInt(e.target.value);
    volumeVal.textContent = `${currentVolume}%`;
    if (ytPlayer && ytPlayer.setVolume) {
      ytPlayer.setVolume(currentVolume);
      if (currentVolume === 0) {
        updateVolumeIcon(true);
      } else {
        ytPlayer.unMute();
        isMuted = false;
        updateVolumeIcon(false);
      }
    }
  });

  muteBtn.addEventListener('click', () => {
    if (!ytPlayer) return;
    isMuted = !isMuted;
    if (isMuted) {
      ytPlayer.mute();
      updateVolumeIcon(true);
    } else {
      ytPlayer.unMute();
      ytPlayer.setVolume(currentVolume);
      updateVolumeIcon(false);
    }
  });

  function updateVolumeIcon(muted) {
    if (muted || currentVolume === 0) {
      volumeIcon.setAttribute('data-lucide', 'volume-x');
    } else if (currentVolume < 50) {
      volumeIcon.setAttribute('data-lucide', 'volume-1');
    } else {
      volumeIcon.setAttribute('data-lucide', 'volume-2');
    }
    lucide.createIcons();
  }

  // Search & Analyze Form Submission
  searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    // Extract video ID to load player immediately
    const idMatch = url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
    if (idMatch && idMatch[1]) {
      initOrLoadVideo(idMatch[1]);
    }

    // UI Loading State
    aiStatusBadge.classList.remove('hidden');
    aiStatusText.textContent = '오디오 다운로드 & Gemini 3.5 전사 중...';
    searchBtn.disabled = true;

    searchResultsList.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-center p-6 text-yt-muted">
        <i data-lucide="loader-2" class="w-8 h-8 animate-spin text-red-500 mb-3"></i>
        <p class="text-xs font-semibold text-white">오디오를 다운로드하고 Gemini가 대본을 생성하고 있습니다...</p>
        <p class="text-[11px] text-yt-muted mt-1">완료되면 단어 검색 및 AI 질의응답이 활성화됩니다.</p>
      </div>
    `;
    timelineList.innerHTML = searchResultsList.innerHTML;
    lucide.createIcons();

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
      });
      const resData = await response.json();

      if (!response.ok || !resData.success) {
        throw new Error(resData.detail || '분석 중 오류가 발생했습니다.');
      }

      currentVideoData = resData.video;
      currentTranscriptData = resData.transcript;
      currentSegments = resData.transcript.segments || [];

      // Render Video Info
      videoInfoCard.classList.remove('hidden');
      videoTitle.textContent = currentVideoData.title;
      videoUploader.textContent = currentVideoData.uploader;
      videoDuration.textContent = `${formatSeconds(currentVideoData.duration)} 영상`;

      aiStatusBadge.classList.remove('animate-pulse');
      if (resData.cached) {
        aiStatusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-amber-950 text-amber-300 border border-amber-800 flex items-center gap-1.5';
        aiStatusText.textContent = '저장된 대본 로드됨 (CSV) ⚡';
      } else {
        aiStatusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1.5';
        aiStatusText.textContent = '대본 분석 & CSV 저장 완료 ✨';
      }

      // Render Timeline
      renderTimeline(currentSegments);
      // Initial Search View (All segments or prompt to search)
      renderSearchResults(currentSegments, "");

    } catch (err) {
      alert(`오류: ${err.message}`);
      aiStatusBadge.classList.add('hidden');
    } finally {
      searchBtn.disabled = false;
    }
  });

  // Render Timeline Segments
  function renderTimeline(segments) {
    if (!segments || segments.length === 0) {
      timelineList.innerHTML = `<p class="text-xs text-yt-muted text-center p-4">추출된 대본이 없습니다.</p>`;
      return;
    }

    timelineList.innerHTML = segments.map((seg) => `
      <div 
        onclick="jumpToSeconds(${seg.seconds})" 
        class="p-2.5 rounded-xl bg-yt-dark hover:bg-yt-hover border border-yt-border/60 hover:border-red-500/50 transition cursor-pointer group flex items-start gap-2.5"
      >
        <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-yt-card text-red-400 group-hover:bg-red-600 group-hover:text-white transition shrink-0">
          ${seg.timestamp}
        </span>
        <div class="flex-1 text-xs">
          ${seg.speaker ? `<span class="font-semibold text-zinc-300 mr-1.5">[${seg.speaker}]</span>` : ''}
          <span class="text-zinc-300 group-hover:text-white leading-relaxed">${escapeHtml(seg.text)}</span>
        </div>
      </div>
    `).join('');
  }

  // In-Video Content Search
  contentSearchInput.addEventListener('input', (e) => {
    const keyword = e.target.value.trim().toLowerCase();
    if (!currentSegments.length) return;

    if (!keyword) {
      renderSearchResults(currentSegments, "");
      return;
    }

    const filtered = currentSegments.filter(s => s.text.toLowerCase().includes(keyword));
    renderSearchResults(filtered, keyword);
  });

  function renderSearchResults(segments, keyword) {
    if (!segments || segments.length === 0) {
      searchResultsList.innerHTML = `
        <div class="h-full flex flex-col items-center justify-center text-center p-6 text-yt-muted">
          <i data-lucide="file-question" class="w-8 h-8 mb-2 opacity-50"></i>
          <p class="text-xs text-white">일치하는 내용을 찾을 수 없습니다.</p>
          <p class="text-[11px] text-yt-muted mt-1">다른 키워드로 검색해 보세요.</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    searchResultsList.innerHTML = segments.map(seg => {
      let highlightedText = escapeHtml(seg.text);
      if (keyword) {
        const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi');
        highlightedText = highlightedText.replace(regex, `<mark class="bg-yellow-400/30 text-yellow-200 px-0.5 rounded font-semibold">$1</mark>`);
      }

      return `
        <div 
          onclick="jumpToSeconds(${seg.seconds})" 
          class="p-3 rounded-xl bg-yt-dark hover:bg-yt-hover border border-yt-border hover:border-red-500 transition cursor-pointer group"
        >
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-red-950 text-red-400 group-hover:bg-red-600 group-hover:text-white transition flex items-center gap-1">
              <i data-lucide="play" class="w-2.5 h-2.5 fill-current"></i>
              ${seg.timestamp}
            </span>
            <span class="text-[10px] text-yt-muted group-hover:text-zinc-300">클릭하여 해당 위치 재생 ❯</span>
          </div>
          <p class="text-xs text-zinc-300 group-hover:text-white leading-relaxed">
            ${highlightedText}
          </p>
        </div>
      `;
    }).join('');
    lucide.createIcons();
  }

  // Ask AI (Gemini 3.8 Flash) Q&A Form
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = chatInput.value.trim();
    if (!question) return;

    if (!currentTranscriptData || !currentTranscriptData.raw_text) {
      alert("영상 대본 분석이 완료된 후 질문할 수 있습니다.");
      return;
    }

    // Append User Message
    appendChatMessage("user", question);
    chatInput.value = "";
    chatSubmitBtn.disabled = true;

    // Loading bubble
    const loadingBubbleId = "loading-bubble-" + Date.now();
    appendChatMessage("ai", `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin inline-block mr-1"></i> Gemini 3.8 Flash가 영상 대본을 분석하여 답변을 작성하고 있습니다...`, loadingBubbleId);
    lucide.createIcons();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          transcript: currentTranscriptData.raw_text,
          video_title: currentVideoData ? currentVideoData.title : ""
        })
      });

      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.detail || "답변 생성 실패");
      }

      // Format Timestamps in AI answer to clickable links
      const formattedAnswer = formatAnswerTimestamps(data.answer);
      updateChatMessage(loadingBubbleId, formattedAnswer);

    } catch (err) {
      updateChatMessage(loadingBubbleId, `<span class="text-rose-400">오류: ${err.message}</span>`);
    } finally {
      chatSubmitBtn.disabled = false;
      lucide.createIcons();
    }
  });

  function appendChatMessage(role, text, bubbleId = "") {
    const isUser = role === "user";
    const div = document.createElement('div');
    div.className = `flex gap-2.5 items-start ${isUser ? 'flex-row-reverse' : ''}`;
    div.innerHTML = `
      <div class="w-6 h-6 rounded-full ${isUser ? 'bg-blue-600' : 'bg-red-600'} flex items-center justify-center text-[10px] text-white shrink-0 mt-0.5">
        ${isUser ? '나' : 'AI'}
      </div>
      <div id="${bubbleId}" class="${isUser ? 'bg-blue-950/70 border-blue-800 text-blue-100' : 'bg-yt-black border-yt-border text-yt-text'} border rounded-xl p-3 text-xs max-w-[85%] leading-relaxed whitespace-pre-wrap">
        ${text}
      </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function updateChatMessage(bubbleId, htmlContent) {
    const elem = document.getElementById(bubbleId);
    if (elem) {
      elem.innerHTML = htmlContent;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  // Convert [MM:SS] in AI answer into clickable spans
  function formatAnswerTimestamps(text) {
    const escaped = escapeHtml(text);
    return escaped.replace(/\[(\d{1,2}:\d{2}(?::\d{2})?)\]/g, (match, p1) => {
      const secs = parseTimestampToSec(p1);
      return `<button onclick="jumpToSeconds(${secs})" class="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-red-950/80 text-red-400 hover:bg-red-600 hover:text-white font-mono font-bold text-[11px] border border-red-800/60 transition cursor-pointer">▶ ${p1}</button>`;
    });
  }

  function parseTimestampToSec(timeStr) {
    const parts = timeStr.split(':').map(Number);
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return parts[0] || 0;
  }

  // Copy Transcript
  copyTranscriptBtn.addEventListener('click', () => {
    if (!currentTranscriptData || !currentTranscriptData.raw_text) return;
    navigator.clipboard.writeText(currentTranscriptData.raw_text).then(() => {
      alert("전체 대본이 클립보드에 복사되었습니다.");
    });
  });

  // Helper functions
  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
});
