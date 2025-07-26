import { useEffect, useState, useRef } from "react";
import { useDrag } from '@use-gesture/react';
import { useModalHistory } from "../hooks/useModalHistory"

export default function GalleryViewer({ adId, onClose, onImageChange, ready }) {
    useModalHistory(onClose);

    const [images, setImages] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true); // Starts as 'Loading...'
    const [progressStatus, setProgressStatus] = useState("Starting...");

    const galleryRef = useRef(null);

    // Fetch gallery image URLs    
    useEffect(() => {
        if (!ready) return;

        const loadImages = async () => {
            try {
                const res = await fetch(`/api/image-count/${adId}`);
                const data = await res.json();
                const count = data.count;

                const urls = Array.from({ length: count }, (_, i) =>
                    `/api/gallery-image/${adId}/${String(i + 1).padStart(2, "0")}`
                );

                setImages(urls);
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch image count", err);
                setLoading(false);
            }
        };

        loadImages();
    }, [adId, ready]);

    
    
    // Poll download progress
    useEffect(() => {
        const interval = setInterval(async () => {
            const res = await fetch(`/api/download-progress/${adId}`);
            const data = await res.json();
            setProgressStatus(data.status);
            if (data.current === data.total && data.total !== 0) {
                clearInterval(interval);                
            }
        }, 500);

        const timeout = setTimeout(() => interval, 1000); // Delays start a bit

        return () => {
            clearTimeout(timeout);
            clearInterval(interval)
        };            
    }, [adId]);

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
        { axis: 'x', swipe: { velocity: 0.2, distance: 30 }}
    );

    // Scrolls image into view
    useEffect(() => {
        if (galleryRef.current) {
            galleryRef.current.scrollIntoView({
                behavior: "smooth",
                block: "center"
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

    {progressStatus && (
    <div className="text-center mt-4 text-sm text-gray-400">{progressStatus}</div>
    )}

    return (
        <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex flex-col items-center justify-center modal-open">
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
                <button
                    onClick={() => {
                        onImageChange(images[currentIndex]);
                        onClose();
                    }}
                    className="absolute top-4 right-4 text-white text-2xl"
                >
                    ✖
                </button>

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
        </div>
    );
}
