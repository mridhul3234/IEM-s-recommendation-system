import React, { useEffect, useRef } from 'react';

const TOTAL_FRAMES = 356;

export default function ScrollFrameBackground() {
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

    // Preload all 356 frames into memory
    const images = [];
    let loadedCount = 0;

    for (let i = 1; i <= TOTAL_FRAMES; i++) {
      const img = new Image();
      const num = String(i).padStart(4, '0');
      img.src = `/iem_frames/frame_${num}.jpg`;
      img.onload = () => {
        loadedCount++;
        if (loadedCount === 1) {
          // Draw first frame immediately
          renderFrame(1);
        }
      };
      images.push(img);
    }
    imagesRef.current = images;

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
        className="w-full h-full opacity-40 transition-opacity duration-300"
      />
      {/* Dark Vignette Overlay for readability */}
      <div className="absolute inset-0 bg-gradient-to-t from-bgBase/80 via-transparent to-bgBase/70"></div>
      <div className="absolute inset-0 bg-gradient-to-r from-bgBase/70 via-transparent to-bgBase/70"></div>
    </div>
  );
}
