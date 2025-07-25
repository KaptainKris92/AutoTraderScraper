import { useEffect, useState, useRef } from "react";

export default function GalleryViewer({ adId, onClose, onImageChange }) {
    const [images, setImages] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true); // Starts as 'Loading...'

    const galleryRef = useRef(null);

    // Fetch image URLs
    useEffect(() => {
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
        }, [adId]);


    // Keyboard navigation
    useEffect(() => {
        const handleKeyDown = (e) => {
        if (e.key === "ArrowLeft") handlePrev();
        if (e.key === "ArrowRight") handleNext();
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [currentIndex, images]);

    // Mobile swipe support
    useEffect(() => {
        let startX = null;

        const onTouchStart = (e) => (startX = e.touches[0].clientX);
        const onTouchEnd = (e) => {
            if (startX === null) return;
            const endX = e.changedTouches[0].clientX;
            const diff = startX - endX;

            if (diff > 50) handleNext();
            else if (diff < -50) handlePrev();

            startX = null;
        };

        const galleryEl = document.getElementById("gallery-container");
        if (!galleryEl) return;

        galleryEl.addEventListener("touchstart", onTouchStart);
        galleryEl.addEventListener("touchend", onTouchEnd);

        return () => {
            galleryEl.removeEventListener("touchstart", onTouchStart);
            galleryEl.removeEventListener("touchend", onTouchEnd);
        };
    }, [currentIndex]);

    // Scrolls image into view
    useEffect(() => {
        if (galleryRef.current) {
            galleryRef.current.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });
        }
    }, [currentIndex]);

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

    return (
        <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex flex-col items-center justify-center">
        {loading ? (
            <div className="text-white text-lg animate-pulse">Loading images...</div>
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
