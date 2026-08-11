import React, { useEffect, useRef } from 'react';

const TOTAL_FRAMES = 356;

export default function ScrollFrameBackground({ opacity = 0.4 }) {
  const canvasRef = useRef(null);
  const imagesRef = useRef([]);
  const stateRef = useRef({
    targetFrame: 1,
    currentFrame: 1,
    rafId: null,
    isLoaded: false
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Create placeholder array for image objects
    const images = new Array(TOTAL_FRAMES);
    imagesRef.current = images;

    let isUnmounted = false;

    // Load initial frame immediately
    const img1 = new Image();
    const num1 = '0001';
    img1.src = `/iem_frames/frame_${num1}.jpg`;
    img1.onload = () => {
      if (!isUnmounted) renderFrame(1);
    };
    images[0] = img1;

    // Progressively load remaining frames in batches during idle periods
    let nextIndexToLoad = 1; // 0-indexed frame 2
    const BATCH_SIZE = 15;

    const loadNextBatch = () => {
      if (isUnmounted || nextIndexToLoad >= TOTAL_FRAMES) return;
      const limit = Math.min(TOTAL_FRAMES, nextIndexToLoad + BATCH_SIZE);
      for (let i = nextIndexToLoad; i < limit; i++) {
        const img = new Image();
        const num = String(i + 1).padStart(4, '0');
        img.src = `/iem_frames/frame_${num}.jpg`;
        images[i] = img;
      }
      nextIndexToLoad = limit;
      if (nextIndexToLoad < TOTAL_FRAMES) {
        if ('requestIdleCallback' in window) {
          window.requestIdleCallback(loadNextBatch, { timeout: 1000 });
        } else {
          setTimeout(loadNextBatch, 100);
        }
      }
    };

    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(loadNextBatch, { timeout: 1000 });
    } else {
      setTimeout(loadNextBatch, 200);
    }

    const resizeCanvas = () => {
      if (!canvas) return;
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      renderFrame(Math.round(stateRef.current.currentFrame));
    };

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    const handleScroll = () => {
      const scrollTop = window.scrollY || document.documentElement.scrollTop;
      const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      const scrollFraction = Math.min(1, Math.max(0, scrollTop / maxScroll));
      
      stateRef.current.targetFrame = 1 + scrollFraction * (TOTAL_FRAMES - 1);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    // 60 FPS Smooth Render Loop with Lerp (Linear Interpolation) Easing
    let animationFrameId;
    const loop = () => {
      const state = stateRef.current;
      // Lerp easing factor (0.18 gives a buttery smooth fluid response)
      const diff = state.targetFrame - state.currentFrame;
      
      if (Math.abs(diff) > 0.01) {
        state.currentFrame += diff * 0.18;
        renderFrame(Math.round(state.currentFrame));
      }

      animationFrameId = requestAnimationFrame(loop);
    };

    loop();

    function renderFrame(frameIdx) {
      if (!canvas || !ctx) return;
      const idx = Math.min(TOTAL_FRAMES, Math.max(1, frameIdx)) - 1;
      const img = imagesRef.current[idx];

      if (img && img.complete && img.naturalWidth > 0) {
        // Draw object-cover math on canvas
        const hRatio = canvas.width / img.naturalWidth;
        const vRatio = canvas.height / img.naturalHeight;
        const ratio = Math.max(hRatio, vRatio);
        const centerShiftX = (canvas.width - img.naturalWidth * ratio) / 2;
        const centerShiftY = (canvas.height - img.naturalHeight * ratio) / 2;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(
          img,
          0, 0, img.naturalWidth, img.naturalHeight,
          centerShiftX, centerShiftY, img.naturalWidth * ratio, img.naturalHeight * ratio
        );
      }
    }

    return () => {
      isUnmounted = true;
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('scroll', handleScroll);
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="fixed inset-0 w-full h-full z-0 pointer-events-none overflow-hidden bg-bgBase">
      {/* Hardware-Accelerated 60 FPS HTML5 Canvas */}
      <canvas 
        ref={canvasRef} 
        style={{ opacity }}
        className="w-full h-full transition-opacity duration-300"
      />
      {/* Minimal Top/Bottom Vignette for Edge Blending */}
      <div className="absolute inset-0 bg-gradient-to-t from-bgBase/10 via-transparent to-bgBase/10"></div>
    </div>
  );
}
