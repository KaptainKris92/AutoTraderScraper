import { useEffect, useState, useRef } from "react";
import { useDrag } from "@use-gesture/react";
import { useModalHistory } from "../hooks/useModalHistory";

export default function GalleryViewer({
  adId,
  onClose,
  onImageChange,
  ready,
  onRegConfirmed,
}) {
  useModalHistory(onClose);

  const [images, setImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true); // Starts as 'Loading...'

  const [progressStatus, setProgressStatus] = useState("Starting...");
  const pollingDoneRef = useRef(false);

  const galleryRef = useRef(null);

  const [ocrResult, setOcrResult] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);

  const [motLoading, setMotLoading] = useState(false);

  // Poll download progress
  useEffect(() => {
    if (!ready || pollingDoneRef.current) return;

    let intervalId;

    const poll = async () => {
      try {
        const res = await fetch(`/api/download-progress/${adId}`);
        const data = await res.json();
        setProgressStatus(data.status);

        const isComplete = data.status === "Complete.";
        const isIdleWithImages = data.status === "Idle" && images.length > 0;
        const isDownloaded = data.current === data.total && data.total !== 0;

        if (isComplete || isIdleWithImages || isDownloaded) {
          pollingDoneRef.current = true;
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error("Progress polling failed", err);
        clearInterval(intervalId);
      }
    };

    intervalId = setInterval(poll, 1000);
    poll(); // Run once immediately

    return () => {
      clearInterval(intervalId);
    };
  }, [adId, ready, images.length]);


  // Fetch gallery images from disk
  useEffect(() => {
    if (!ready) return;

    const fetchImages = async () => {
      try {
        const res = await fetch(`/api/image-count/${adId}`);
        const data = await res.json();
        const count = data.count;

        if (count > 0) {
          const urls = Array.from(
            { length: count },
            (_, i) =>
              `/api/gallery-image/${adId}/${String(i + 1).padStart(2, "0")}`
          );
          setImages(urls);
        } else {
          setImages([]);
        }
      } catch (err) {
        console.error("Failed to fetch gallery images:", err);
        setImages([]);
      }
    };

    fetchImages();
  }, [adId, ready]);

  // Set loading to false when download is complete
  useEffect(() => {
    if (!ready) return;

    // Case 0: already downloaded, but progress status is Idle
    if (progressStatus === "Idle" && images.length > 0) {
      setLoading(false);
      return;
    }

    // Case 1: explicit "Complete." string
    if (progressStatus === "Complete.") {
      setLoading(false);
      return;
    }

    // Case 2: downloading X/X images
    if (progressStatus.toLowerCase().includes("downloading")) {
      const match = progressStatus.match(/(\d+)\/(\d+)/);
      if (match) {
        const [, current, total] = match.map(Number);
        if (current === total && total !== 0) {
          setLoading(false);
        }
      }
    }
  }, [progressStatus, ready, images.length]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, images, onClose]);

  // Mobile swipe to move
  const bind = useDrag(
    ({ swipe: [swipeX] }) => {
      if (swipeX === -1) handleNext();
      if (swipeX === 1) handlePrev();
    },
    { axis: "x", swipe: { velocity: 0.2, distance: 30 } }
  );

  // Scrolls image into view
  useEffect(() => {
    if (galleryRef.current) {
      galleryRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [currentIndex]);

  // Reset progress status on adId change
  useEffect(() => {
    setProgressStatus("Starting...");
    setCurrentIndex(0);
  }, [adId]);

  const handlePrev = () => {
    setCurrentIndex((i) => Math.max(i - 1, 0));
  };

  const handleNext = () => {
    setCurrentIndex((i) => Math.min(i + 1, images.length - 1));
  };

  const handleInput = (e) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val) && val >= 1 && val <= images.length) {
      setCurrentIndex(val - 1);
    }
  };

  const handleOCRCheck = async () => {
    setOcrLoading(true);
    setShowConfirm(false);

    try {
      const imgNumber = String(currentIndex + 1).padStart(2, "0");
      const res = await fetch(`/api/ocr-single/${adId}/${imgNumber}`);
      const data = await res.json();

      console.log(adId, imgNumber, data);

      if (!data || !data.plates || data.plates.length === 0) {
        alert("No registration plates found.");
      } else {
        setOcrResult(data.plates[0]); // Picks first results
        setShowConfirm(true);
      }
    } catch (err) {
      console.error("OCR failed:", err);
      alert("OCR failed");
    } finally {
      setOcrLoading(false);
    }
  };

  const handleConfirmReg = async () => {
    setMotLoading(true);
    setShowConfirm(false);

    try {
      // Fetch MOT history
      const res = await fetch(`/api/mot_history/query?reg=${ocrResult}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      // Save MOT history
      await fetch("/api/mot_history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          registration: ocrResult.replace(/\s+/g, "").toUpperCase(),
          data,
          ad_id: adId,
        }),
      });

      // Notify parent to refresh
      if (onRegConfirmed) onRegConfirmed();

      alert("✅ MOT history saved and linked.");
      onImageChange(images[currentIndex]);
      setShowConfirm(false);
      onClose();
    } catch (err) {
      console.error("Failed to confirm reg:", err);
      alert("Failed to fetch and bind MOT data.");
    } finally {
      setMotLoading(true);
    }
  };

  {
    progressStatus && (
      <div className="text-center mt-4 text-sm text-gray-400">
        {progressStatus}
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex flex-col items-center justify-center modal-open">
      {ocrLoading && (
        <div className="absolute top-4 left-4 bg-white/90 px-4 py-2 rounded shadow-lg animate-pulse z-50">
          Searching for registration plate...
        </div>
      )}

      {motLoading && (
        <div className="absolute top-16 left-4 bg-white/90 px-4 py-2 rounded shadow-lg animate-pulse z-50">
          Fetching MOT history...
        </div>
      )}

      {loading ? (
        <div className="text-white text-center space-y-2">
          <div className="text-lg animate-pulse">Loading images...</div>
          {progressStatus && (
            <div className="text-sm text-gray-300">{progressStatus}</div>
          )}
        </div>
      ) : images.length === 0 ? (
        <div className="text-white text-lg">No images found.</div>
      ) : (
        <>
          {/* Close button */}
          <button
            onClick={() => {
              onImageChange(images[currentIndex]);
              onClose();
            }}
            className="absolute top-4 right-4 text-white text-2xl"
          >
            ✖
          </button>

          {/* Image */}
          <div
            id="gallery-container"
            {...bind()}
            ref={galleryRef}
            className="w-full h-full flex items-center justify-center"
          >
            <img
              src={images[currentIndex]}
              alt={`Image ${currentIndex + 1}`}
              className="max-w-full max-h-[80vh] object-contain"
            />
          </div>

          {/* OCR Button */}
          <div className="mt-4 flex justify-center">
            <button
              onClick={handleOCRCheck}
              className="bg-yellow-500 text-white px-4 py-2 rounded text-sm shadow"
            >
              Find reg in image
            </button>
          </div>

          {/* Left and right buttons + image index */}
          <div className="flex items-center gap-4 mt-4">
            <button
              onClick={handlePrev}
              disabled={currentIndex === 0}
              className="text-white text-xl"
            >
              ◀
            </button>

            <input
              type="number"
              min={1}
              max={images.length}
              value={currentIndex + 1}
              onChange={handleInput}
              className="w-16 text-center rounded bg-gray-800 text-white"
            />

            <span className="text-white">/ {images.length}</span>

            <button
              onClick={handleNext}
              disabled={currentIndex === images.length - 1}
              className="text-white text-xl"
            >
              ▶
            </button>
          </div>
        </>
      )}

      {/* Confirmation box */}
      {showConfirm && (
        <div className="absolute bottom-2 left-2 bg-white/90 p-3 rounded shadow-lg text-sm space-y-2 z-50">
          <p>
            Found reg: <strong>{ocrResult}</strong>
          </p>
          <div className="flex gap-2">
            <button
              className="bg-green-600 text-white px-3 py-1 rounded"
              onClick={handleConfirmReg}
            >
              Confirm & Fetch MOT
            </button>
            <button
              className="bg-gray-300 text-black px-3 py-1 rounded"
              onClick={() => setShowConfirm(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
