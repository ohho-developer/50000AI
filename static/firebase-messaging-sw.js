// Firebase Messaging Service Worker
// This file is required for Firebase Cloud Messaging
// Even if not using FCM, browsers may request this file

console.log('Firebase messaging service worker loaded');

// Basic service worker registration
self.addEventListener('install', function(event) {
    console.log('Service worker installing');
});

self.addEventListener('activate', function(event) {
    console.log('Service worker activated');
});

// Handle push notifications (if needed in the future)
self.addEventListener('push', function(event) {
    console.log('Push message received');
    // Add push notification handling here if needed
});
