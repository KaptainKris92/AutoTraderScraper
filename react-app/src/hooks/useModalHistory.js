import { useEffect } from "react";

// Allows 'Back' to close modals.
export function useModalHistory(onClose) {
    useEffect(() => {
        const modalState = { modal: true };

        // Push a state to indicate modal is open
        if (window.history.state?.modal !== true) {
            window.history.pushState(modalState, "");
        }

        const handlePopState = (e) => {
            // If navigating away from a modal state, close the modal
            if (window.history.state?.modal !== true) {
                onClose();
            }
        };

        window.addEventListener("popstate", handlePopState);

        return () => {
            window.removeEventListener("popstate", handlePopState);
        };
    }, [onClose]);
}
