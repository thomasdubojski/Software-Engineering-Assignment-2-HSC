const CACHE_NAME = "assignment-tracker-v2";

const FILES_TO_CACHE = [
    "/",
    "/login",
    "/create-account",
    "/calendar",
    "/offline",

    "/static/css/style.css",
    "/static/js/app.js",

    "/static/images/Assignment Tracker Logo (512 x 512 px).png",
    "/static/images/Assignment Tracker Logo - No Text (192 x 192 px).png"
];

// Install
self.addEventListener("install", event => {

    event.waitUntil(

        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(FILES_TO_CACHE);
        })

    );

});

// Activate
self.addEventListener("activate", event => {

    event.waitUntil(

        caches.keys().then(keys => {

            return Promise.all(

                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))

            );

        })

    );

});

// Fetch
self.addEventListener("fetch", event => {

    const requestURL = new URL(event.request.url);

    // Never cache authentication or POST requests
    if (
        event.request.method !== "GET" ||
        requestURL.pathname.includes("/login") ||
        requestURL.pathname.includes("/logout") ||
        requestURL.pathname.includes("/create-account")
    ) {

        return;

    }


    event.respondWith(

        fetch(event.request)
            .catch(() => caches.match(event.request))

    );

});